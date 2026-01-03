import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowDown, CheckCircle2, ChevronDown, ChevronUp, ShieldCheck } from "lucide-react";
import { DecisionImpact } from "@/lib/types";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface ImpactThisWeekProps {
    impacts: DecisionImpact[];
}

export function ImpactThisWeek({ impacts }: ImpactThisWeekProps) {
    const [expandedId, setExpandedId] = useState<string | null>(null);

    if (!impacts.length) {
        return null; // Don't show if empty
    }

    const totalReduction = impacts.reduce((sum, i) => sum + i.risk_delta_points, 0);

    return (
        <Card className="border-emerald-900/20 bg-emerald-950/5 backdrop-blur-sm">
            <CardHeader className="pb-3 border-b border-white/5">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-medium flex items-center gap-2">
                        <ShieldCheck className="h-4 w-4 text-emerald-500" />
                        Impact This Week
                    </CardTitle>
                    <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 gap-1">
                        <ArrowDown className="h-3 w-3" />
                        {totalReduction} points reduced
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="pt-0">
                <div className="divide-y divide-white/5">
                    {impacts.map((impact) => (
                        <div key={impact.id} className="py-3">
                            <div
                                className="flex items-center justify-between group cursor-pointer"
                                onClick={() => setExpandedId(expandedId === impact.id ? null : impact.id)}
                            >
                                <div className="flex items-center gap-3">
                                    <div className="h-6 w-6 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                                    </div>
                                    <div>
                                        <h4 className="text-sm font-medium text-gray-200 group-hover:text-emerald-400 transition-colors">
                                            {impact.title}
                                        </h4>
                                        {impact.asset_name && (
                                            <p className="text-xs text-gray-500 mt-0.5">{impact.asset_name}</p>
                                        )}
                                    </div>
                                </div>

                                <div className="flex items-center gap-4">
                                    <span className="text-sm font-medium text-emerald-400">-{impact.risk_delta_points} pts</span>
                                    {expandedId === impact.id ? (
                                        <ChevronUp className="h-4 w-4 text-gray-500" />
                                    ) : (
                                        <ChevronDown className="h-4 w-4 text-gray-500" />
                                    )}
                                </div>
                            </div>

                            <div className={cn(
                                "grid transition-all duration-200 ease-in-out text-sm text-gray-400 pl-9 overflow-hidden",
                                expandedId === impact.id ? "grid-rows-[1fr] opacity-100 mt-2" : "grid-rows-[0fr] opacity-0"
                            )}>
                                <div className="min-h-0">
                                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Evidence</p>
                                    <ul className="space-y-1">
                                        {impact.evidence_signal_ids && impact.evidence_signal_ids.length > 0 ? (
                                            impact.evidence_signal_ids.map((id, idx) => (
                                                <li key={idx} className="flex items-center gap-2">
                                                    <span className="w-1 h-1 rounded-full bg-gray-600"></span>
                                                    Signal ID: <span className="font-mono text-gray-500">{id.substring(0, 8)}...</span>
                                                </li>
                                            ))
                                        ) : (
                                            <li className="italic text-gray-600">No specific evidence linked</li>
                                        )}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
