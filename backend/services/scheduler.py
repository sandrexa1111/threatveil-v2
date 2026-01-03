"""
Continuous Monitoring Scheduler

Background scheduler for running scheduled asset scans.
Uses APScheduler for job management with configurable intervals.

The scheduler:
- Runs every 5 minutes to check for due scans
- Queries assets where next_scan_at <= now() and status = 'active'
- Triggers scans for each due asset
- Updates schedule with new next_run_at based on frequency
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Asset, ScanSchedule, Scan, AuditLog

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> Optional[BackgroundScheduler]:
    """Get the global scheduler instance."""
    return _scheduler


def calculate_next_run(frequency: str, from_time: Optional[datetime] = None) -> datetime:
    """
    Calculate next run time based on frequency.
    
    Args:
        frequency: 'daily', 'weekly', or 'monthly'
        from_time: Base time (defaults to now)
    
    Returns:
        Next run datetime
    """
    base = from_time or datetime.utcnow()
    
    if frequency == 'daily':
        return base + timedelta(days=1)
    elif frequency == 'weekly':
        return base + timedelta(weeks=1)
    elif frequency == 'monthly':
        return base + timedelta(days=30)
    else:
        # Manual or unknown - set far future
        return base + timedelta(days=365)


def run_due_scans():
    """
    Check for and execute due scans.
    
    This is the main scheduler job that runs periodically.
    It finds all assets that are due for scanning and triggers scans.
    """
    logger.info("Scheduler: Checking for due scans...")
    
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Find assets due for scanning
        due_assets = db.query(Asset).filter(
            Asset.status == 'active',
            Asset.next_scan_at <= now,
            Asset.scan_frequency != 'manual'
        ).all()
        
        if not due_assets:
            logger.debug("Scheduler: No assets due for scanning")
            return
        
        logger.info(f"Scheduler: Found {len(due_assets)} assets due for scanning")
        
        for asset in due_assets:
            try:
                trigger_asset_scan(db, asset)
            except Exception as e:
                logger.error(f"Scheduler: Failed to scan asset {asset.id}: {e}")
                # Update schedule with error
                schedule = db.query(ScanSchedule).filter(
                    ScanSchedule.asset_id == asset.id,
                    ScanSchedule.status == 'active'
                ).first()
                if schedule:
                    schedule.error_count += 1
                    schedule.last_error = str(e)
                    db.commit()
        
    except Exception as e:
        logger.error(f"Scheduler: Error in run_due_scans: {e}")
    finally:
        db.close()


def trigger_asset_scan(db: Session, asset: Asset):
    """
    Trigger a scan for a specific asset.
    
    Currently supports:
    - domain: Triggers full domain scan
    - github_org: Triggers GitHub scan (via domain scan with github_org param)
    
    Cloud accounts and SaaS vendors are logged but not scanned (metadata only).
    """
    logger.info(f"Scheduler: Triggering scan for asset {asset.id} ({asset.type}: {asset.name})")
    
    if asset.type == 'domain':
        # Import here to avoid circular imports
        from ..routes.scan import perform_scan
        
        # Create scan request
        scan_result = perform_scan(
            domain=asset.name,
            github_org=None,
            db=db,
            org_id=asset.org_id
        )
        
        # Update asset with scan results
        asset.last_scan_at = datetime.utcnow()
        asset.next_scan_at = calculate_next_run(asset.scan_frequency)
        asset.last_risk_score = scan_result.get('risk_score')
        
        # Update schedule if exists
        update_schedule_after_scan(db, asset, scan_result.get('id'))
        
        # Log the action
        log_scan_action(db, asset, scan_result.get('id'))
        
    elif asset.type == 'github_org':
        # GitHub orgs are scanned via domain scan with github_org parameter
        # For now, we just update the schedule
        asset.last_scan_at = datetime.utcnow()
        asset.next_scan_at = calculate_next_run(asset.scan_frequency)
        
        logger.info(f"Scheduler: GitHub org {asset.name} - scanning not yet implemented")
        
    elif asset.type in ('cloud_account', 'saas_vendor'):
        # Metadata-only assets - just update timestamps
        asset.last_scan_at = datetime.utcnow()
        asset.next_scan_at = calculate_next_run(asset.scan_frequency)
        
        logger.info(f"Scheduler: {asset.type} {asset.name} - metadata only, no scan performed")
    
    db.commit()


def update_schedule_after_scan(db: Session, asset: Asset, scan_id: Optional[str]):
    """Update the scan schedule after a successful scan."""
    schedule = db.query(ScanSchedule).filter(
        ScanSchedule.asset_id == asset.id,
        ScanSchedule.status == 'active'
    ).first()
    
    if schedule:
        schedule.last_run_at = datetime.utcnow()
        schedule.next_run_at = asset.next_scan_at
        schedule.last_scan_id = scan_id
        schedule.run_count += 1
        schedule.last_error = None  # Clear any previous error
        db.commit()


def log_scan_action(db: Session, asset: Asset, scan_id: Optional[str]):
    """Log the scheduled scan action to audit log."""
    audit_log = AuditLog(
        org_id=asset.org_id,
        action='scheduled_scan',
        resource_type='asset',
        resource_id=asset.id,
        details={
            'asset_name': asset.name,
            'asset_type': asset.type,
            'scan_id': scan_id,
            'frequency': asset.scan_frequency
        }
    )
    db.add(audit_log)
    db.commit()


def start_scheduler(interval_minutes: int = 5):
    """
    Start the background scheduler.
    
    Args:
        interval_minutes: How often to check for due scans (default: 5 minutes)
    """
    global _scheduler
    
    if _scheduler is not None:
        logger.warning("Scheduler already running")
        return
    
    _scheduler = BackgroundScheduler()
    
    # Add the main job to check for due scans
    _scheduler.add_job(
        run_due_scans,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id='run_due_scans',
        name='Check and run due asset scans',
        replace_existing=True
    )
    
    _scheduler.start()
    logger.info(f"Scheduler started - checking for due scans every {interval_minutes} minutes")


def stop_scheduler():
    """Stop the background scheduler gracefully."""
    global _scheduler
    
    if _scheduler is None:
        logger.warning("Scheduler not running")
        return
    
    _scheduler.shutdown(wait=True)
    _scheduler = None
    logger.info("Scheduler stopped")


def get_scheduler_status() -> dict:
    """Get current scheduler status."""
    global _scheduler
    
    if _scheduler is None:
        return {
            'running': False,
            'jobs': []
        }
    
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
        })
    
    return {
        'running': _scheduler.running,
        'jobs': jobs
    }
