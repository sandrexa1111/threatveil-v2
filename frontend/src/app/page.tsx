'use client';

import { LandingHeader } from '@/components/LandingHeader';
import { HeroSection } from '@/components/landing/HeroSection';
import { WhatWeDoSection } from '@/components/landing/WhatWeDoSection';
import { AudienceSection } from '@/components/landing/AudienceSection';
import { ComparisonSection } from '@/components/landing/ComparisonSection';
import { HowItWorksSection } from '@/components/landing/HowItWorksSection';
import { DifferentiatorsSection } from '@/components/landing/DifferentiatorsSection';
import { PricingSection } from '@/components/landing/PricingSection';
import { TrustSection } from '@/components/landing/TrustSection';
import { FinalCTASection } from '@/components/landing/FinalCTASection';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950">
      <LandingHeader />
      {/* Add padding-top to account for fixed header */}
      <main className="pt-16">
        {/* 1. Hero */}
        <HeroSection />

        {/* 2. What We Do (Collect → Decide → Act) */}
        <WhatWeDoSection />

        {/* 3. Who It's For (Audience personas) */}
        <AudienceSection />

        {/* 4. Why Tools Fail (Problem/Solution) */}
        <ComparisonSection />

        {/* 5. How It Works (Timeline) */}
        <HowItWorksSection />

        {/* 6. What Makes Us Different (Value props) */}
        <DifferentiatorsSection />

        {/* 7. Pricing */}
        <PricingSection />

        {/* 8. Trust & Safety */}
        <TrustSection />

        {/* 9. Final CTA */}
        <FinalCTASection />
      </main>
    </div>
  );
}
