'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Globe, Github, Cloud, Package } from 'lucide-react';
import type { AssetCreate, AssetType, ScanFrequency } from '@/lib/types';

interface AddAssetModalProps {
    onAdd: (asset: AssetCreate) => Promise<void>;
    isLoading?: boolean;
}

const assetTypeConfig: Record<AssetType, { icon: React.ReactNode; label: string; placeholder: string; externalIdLabel?: string }> = {
    domain: {
        icon: <Globe className="h-4 w-4" />,
        label: 'Domain',
        placeholder: 'example.com',
    },
    github_org: {
        icon: <Github className="h-4 w-4" />,
        label: 'GitHub Organization',
        placeholder: 'my-org',
    },
    cloud_account: {
        icon: <Cloud className="h-4 w-4" />,
        label: 'Cloud Account',
        placeholder: 'Production AWS',
        externalIdLabel: 'Account ID / Tenant ID',
    },
    saas_vendor: {
        icon: <Package className="h-4 w-4" />,
        label: 'SaaS Vendor',
        placeholder: 'Salesforce',
    },
};

export function AddAssetModal({ onAdd, isLoading }: AddAssetModalProps) {
    const [open, setOpen] = useState(false);
    const [type, setType] = useState<AssetType>('domain');
    const [name, setName] = useState('');
    const [externalId, setExternalId] = useState('');
    const [scanFrequency, setScanFrequency] = useState<ScanFrequency>('weekly');
    const [category, setCategory] = useState('');
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!name.trim()) {
            setError('Name is required');
            return;
        }

        try {
            const asset: AssetCreate = {
                type,
                name: name.trim(),
                scan_frequency: scanFrequency,
            };

            if (externalId.trim()) {
                asset.external_id = externalId.trim();
            }

            if (type === 'saas_vendor' && category.trim()) {
                asset.properties = { category: category.trim() };
            }

            if (type === 'cloud_account') {
                asset.properties = { provider: category || 'aws' };
            }

            await onAdd(asset);

            // Reset form
            setName('');
            setExternalId('');
            setCategory('');
            setType('domain');
            setScanFrequency('weekly');
            setOpen(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to add asset');
        }
    };

    const config = assetTypeConfig[type];

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button className="bg-purple-600 hover:bg-purple-700 text-white">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Asset
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px] bg-slate-900 border-slate-800">
                <DialogHeader>
                    <DialogTitle className="text-white">Add New Asset</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                    {/* Asset Type */}
                    <div className="space-y-2">
                        <Label className="text-slate-300">Asset Type</Label>
                        <Select value={type} onValueChange={(v) => setType(v as AssetType)}>
                            <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-800 border-slate-700">
                                {Object.entries(assetTypeConfig).map(([key, cfg]) => (
                                    <SelectItem key={key} value={key} className="text-white hover:bg-slate-700">
                                        <div className="flex items-center gap-2">
                                            {cfg.icon}
                                            {cfg.label}
                                        </div>
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Name */}
                    <div className="space-y-2">
                        <Label className="text-slate-300">{config.label} Name</Label>
                        <Input
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder={config.placeholder}
                            className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
                        />
                    </div>

                    {/* External ID (for cloud accounts) */}
                    {config.externalIdLabel && (
                        <div className="space-y-2">
                            <Label className="text-slate-300">{config.externalIdLabel}</Label>
                            <Input
                                value={externalId}
                                onChange={(e) => setExternalId(e.target.value)}
                                placeholder="123456789012"
                                className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
                            />
                        </div>
                    )}

                    {/* Cloud Provider (for cloud accounts) */}
                    {type === 'cloud_account' && (
                        <div className="space-y-2">
                            <Label className="text-slate-300">Cloud Provider</Label>
                            <Select value={category || 'aws'} onValueChange={setCategory}>
                                <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="bg-slate-800 border-slate-700">
                                    <SelectItem value="aws" className="text-white hover:bg-slate-700">AWS</SelectItem>
                                    <SelectItem value="azure" className="text-white hover:bg-slate-700">Azure</SelectItem>
                                    <SelectItem value="gcp" className="text-white hover:bg-slate-700">GCP</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    )}

                    {/* Category (for SaaS vendors) */}
                    {type === 'saas_vendor' && (
                        <div className="space-y-2">
                            <Label className="text-slate-300">Category</Label>
                            <Select value={category} onValueChange={setCategory}>
                                <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                                    <SelectValue placeholder="Select category" />
                                </SelectTrigger>
                                <SelectContent className="bg-slate-800 border-slate-700">
                                    <SelectItem value="crm" className="text-white hover:bg-slate-700">CRM</SelectItem>
                                    <SelectItem value="payments" className="text-white hover:bg-slate-700">Payments</SelectItem>
                                    <SelectItem value="analytics" className="text-white hover:bg-slate-700">Analytics</SelectItem>
                                    <SelectItem value="communication" className="text-white hover:bg-slate-700">Communication</SelectItem>
                                    <SelectItem value="security" className="text-white hover:bg-slate-700">Security</SelectItem>
                                    <SelectItem value="other" className="text-white hover:bg-slate-700">Other</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    )}

                    {/* Scan Frequency */}
                    <div className="space-y-2">
                        <Label className="text-slate-300">Scan Frequency</Label>
                        <Select value={scanFrequency} onValueChange={(v) => setScanFrequency(v as ScanFrequency)}>
                            <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-800 border-slate-700">
                                <SelectItem value="daily" className="text-white hover:bg-slate-700">Daily (Critical)</SelectItem>
                                <SelectItem value="weekly" className="text-white hover:bg-slate-700">Weekly (Default)</SelectItem>
                                <SelectItem value="monthly" className="text-white hover:bg-slate-700">Monthly (Low-risk)</SelectItem>
                                <SelectItem value="manual" className="text-white hover:bg-slate-700">Manual Only</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    {error && (
                        <p className="text-sm text-red-400">{error}</p>
                    )}

                    <div className="flex justify-end gap-3 pt-4">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => setOpen(false)}
                            className="border-slate-700 text-slate-300 hover:bg-slate-800"
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            disabled={isLoading}
                            className="bg-purple-600 hover:bg-purple-700 text-white"
                        >
                            {isLoading ? 'Adding...' : 'Add Asset'}
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
