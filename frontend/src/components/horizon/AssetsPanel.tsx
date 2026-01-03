import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AssetRiskSummary } from "@/lib/types";
import { Globe, Database, ArrowUp, ArrowDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface AssetsPanelProps {
    assets: AssetRiskSummary[];
}

export function AssetsPanel({ assets }: AssetsPanelProps) {
    if (!assets.length) {
        return (
            <Card className="border-gray-800 bg-[#111827]/80 backdrop-blur-sm">
                <CardHeader>
                    <CardTitle className="text-base text-white/90">Asset Risk Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-gray-500">No assets monitored yet.</p>
                </CardContent>
            </Card>
        );
    }

    // Top 5 highest risk
    const topRisky = [...assets].sort((a, b) => b.risk_score - a.risk_score).slice(0, 5);

    // Top 3 movers (absolute trend value)
    const topMovers = [...assets]
        .filter(a => a.trend !== 0)
        .sort((a, b) => Math.abs(b.trend) - Math.abs(a.trend))
        .slice(0, 3);

    const getRiskColor = (score: number) => {
        if (score > 70) return "text-red-400";
        if (score > 40) return "text-yellow-400";
        return "text-emerald-400";
    };

    const getRiskBg = (score: number) => {
        if (score > 70) return "bg-red-500/10";
        if (score > 40) return "bg-yellow-500/10";
        return "bg-emerald-500/10";
    };

    const getTrendIcon = (trend: number) => {
        if (trend > 0) return <ArrowUp className="h-3 w-3 text-red-400" />;
        if (trend < 0) return <ArrowDown className="h-3 w-3 text-emerald-400" />;
        return <Minus className="h-3 w-3 text-gray-500" />;
    };

    return (
        <Card className="border-gray-800 bg-[#111827]/80 backdrop-blur-sm h-full flex flex-col">
            <CardHeader className="pb-3 border-b border-gray-800/50">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-medium text-white/90">Asset Risk Breakdown</CardTitle>
                    <Badge variant="secondary" className="bg-gray-800 text-gray-400 font-normal">
                        {assets.length} Monitored
                    </Badge>
                </div>
            </CardHeader>

            <CardContent className="pt-4 flex-1 flex flex-col gap-6">
                {/* Risk Distribution */}
                <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Highest Risk Assets</h4>
                    <div className="space-y-3">
                        {topRisky.map((asset) => (
                            <div key={asset.asset_id} className="flex items-center justify-between group">
                                <div className="flex items-center gap-3">
                                    <div className={cn("p-1.5 rounded-md", getRiskBg(asset.risk_score))}>
                                        {asset.asset_type === 'domain' ? (
                                            <Globe className={cn("h-4 w-4", getRiskColor(asset.risk_score))} />
                                        ) : (
                                            <Database className={cn("h-4 w-4", getRiskColor(asset.risk_score))} />
                                        )}
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-sm font-medium text-gray-200 group-hover:text-white transition-colors">
                                            {asset.name}
                                        </span>
                                        <span className="text-[10px] text-gray-500 uppercase">{asset.asset_type}</span>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <span className={cn("text-sm font-bold block", getRiskColor(asset.risk_score))}>
                                        {asset.risk_score}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Movers */}
                {topMovers.length > 0 && (
                    <div>
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Top Movers (7d)</h4>
                        <div className="space-y-3">
                            {topMovers.map((asset) => (
                                <div key={asset.asset_id} className="flex items-center justify-between">
                                    <span className="text-sm text-gray-300 truncate max-w-[150px]">{asset.name}</span>
                                    <div className="flex items-center gap-1.5 bg-gray-900/50 px-2 py-1 rounded border border-gray-800">
                                        {getTrendIcon(asset.trend)}
                                        <span className={cn(
                                            "text-xs font-medium",
                                            asset.trend > 0 ? "text-red-400" : (asset.trend < 0 ? "text-emerald-400" : "text-gray-400")
                                        )}>
                                            {asset.trend > 0 ? '+' : ''}{asset.trend}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
