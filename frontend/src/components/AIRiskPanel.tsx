'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Brain, Bot, Key, AlertTriangle, ShieldCheck, Terminal, MessageSquare, Loader2, Shield } from 'lucide-react';
import { LoadingSpinner } from './LoadingSpinner';
import { motion, AnimatePresence } from 'framer-motion';

interface AIRiskPanelProps {
  aiScore: number;
  aiSummary: string;
  tools: string[];
  agents: string[];
  leaks: Array<{
    key_type?: string;
    repository?: string;
    path?: string;
    url?: string;
  }>;
  hasLakera?: boolean;
  scanId?: string;
}

export function AIRiskPanel({ aiScore, aiSummary, tools, agents, leaks, hasLakera = false, scanId }: AIRiskPanelProps) {
  const [activeTab, setActiveTab] = useState('tools');
  const [explanation, setExplanation] = useState<string | null>(null);
  const [isExplaining, setIsExplaining] = useState(false);
  const [explainError, setExplainError] = useState<string | null>(null);

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-red-400';
    if (score >= 30) return 'text-amber-400';
    return 'text-emerald-400';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 70) return 'High Exposure';
    if (score >= 30) return 'Moderate Exposure';
    return 'Low Exposure';
  };

  const handleExplain = async () => {
    if (!scanId) return;

    setIsExplaining(true);
    // Clear any previous error (we'll use fallback instead of showing errors)
    setExplainError(null);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
      const res = await fetch(`${baseUrl}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scan_id: scanId,
          message: "Explain the AI risk analysis in simpler terms for a non-technical audience."
        })
      });

      if (!res.ok) throw new Error('Failed to get explanation');

      const data = await res.json();
      // Truncate very long responses
      const response = data.response || data.message || '';
      setExplanation(response.length > 500 ? response.slice(0, 500) + '...' : response);
    } catch (err) {
      // Use deterministic fallback explanation instead of showing error
      const fallback = generateFallbackExplanation(tools, agents, leaks);
      setExplanation(fallback);
    } finally {
      setIsExplaining(false);
    }
  };

  /**
   * Generates a deterministic fallback explanation based on scan data.
   * Used when LLM API fails — never shows raw errors to users.
   */
  function generateFallbackExplanation(tools: string[], agents: string[], leaks: AIRiskPanelProps['leaks']): string {
    if (leaks.length > 0) {
      return `We detected ${leaks.length} exposed credential${leaks.length > 1 ? 's' : ''} in public repositories. These should be rotated immediately as attackers actively scan for such leaks. After rotation, revoke the old credentials and audit access logs for unauthorized usage.`;
    }
    if (agents.length > 0) {
      return `Your organization uses ${agents.length} agentic AI framework${agents.length > 1 ? 's' : ''}. These systems can autonomously access internal APIs and databases. Review their access permissions and ensure they operate with minimal required privileges.`;
    }
    if (tools.length > 0) {
      return `We found ${tools.length} AI tool${tools.length > 1 ? 's' : ''} publicly associated with your organization. While not immediately dangerous, this increases your attack surface. Maintain an inventory of approved AI tools and monitor for shadow AI usage.`;
    }
    return 'No significant AI exposure detected. Your organization has a clean AI security posture with no publicly visible AI tools, agent frameworks, or credential leaks.';
  }

  return (
    <Card className="h-full border-gray-800 bg-[#111827]/80 backdrop-blur-sm rounded-2xl shadow-sm flex flex-col">
      <CardHeader className="pb-2 border-b border-gray-800/50">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base font-semibold text-white/95 flex items-center gap-2">
              <Brain className="h-4 w-4 text-purple-500" />
              AI Exposure
            </CardTitle>
            <p className="text-xs text-gray-500 mt-1">{getScoreLabel(aiScore)}</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-lg font-bold ${getScoreColor(aiScore)}`}>{aiScore}</span>
            <span className="text-xs text-gray-500 font-medium uppercase">Score</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 pt-6 flex flex-col gap-6">
        {/* Tabs Section */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full flex-1 flex flex-col">
          <TabsList className="w-full grid grid-cols-3 bg-gray-900/50 border border-gray-800 p-1 rounded-lg mb-4">
            <TabsTrigger
              value="tools"
              className="text-xs font-medium data-[state=active]:bg-gray-800 data-[state=active]:text-white text-gray-400"
            >
              AI Tools ({tools.length})
            </TabsTrigger>
            <TabsTrigger
              value="agents"
              className="text-xs font-medium data-[state=active]:bg-gray-800 data-[state=active]:text-white text-gray-400"
            >
              Agents ({agents.length})
            </TabsTrigger>
            <TabsTrigger
              value="keys"
              className={`text-xs font-medium data-[state=active]:bg-gray-800 data-[state=active]:text-white ${leaks.length > 0 ? 'text-red-400' : 'text-gray-400'}`}
            >
              Key Leaks ({leaks.length})
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 min-h-[140px]">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
              >
                {activeTab === 'tools' && (
                  <div className="space-y-3">
                    {tools.length > 0 ? (
                      <div className="grid grid-cols-1 gap-2">
                        {tools.map((tool, i) => (
                          <div key={i} className="flex items-center gap-3 p-2 rounded-md bg-gray-800/30 border border-gray-800/50">
                            <div className="h-8 w-8 rounded-full bg-cyan-500/10 flex items-center justify-center shrink-0">
                              <Terminal className="h-4 w-4 text-cyan-400" />
                            </div>
                            <span className="text-sm text-gray-300 font-medium">{tool}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <PositiveEmptyState
                        title="No Public AI Tools Detected"
                        description="Your organization has no publicly visible AI tool usage — this reduces your attack surface."
                      />
                    )}
                  </div>
                )}

                {activeTab === 'agents' && (
                  <div className="space-y-3">
                    {agents.length > 0 ? (
                      <div className="grid grid-cols-1 gap-2">
                        {agents.map((agent, i) => (
                          <div key={i} className="flex items-center gap-3 p-2 rounded-md bg-orange-500/5 border border-orange-500/20">
                            <div className="h-8 w-8 rounded-full bg-orange-500/10 flex items-center justify-center shrink-0">
                              <Bot className="h-4 w-4 text-orange-400" />
                            </div>
                            <span className="text-sm text-orange-200 font-medium">{agent}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <PositiveEmptyState
                        title="No Agent Frameworks Exposed"
                        description="No agentic AI systems detected publicly — this prevents automated exploitation of internal APIs."
                      />
                    )}
                    {agents.length > 0 && (
                      <p className="text-xs text-orange-400/70 mt-2 flex items-center gap-1">
                        <AlertTriangle className="h-3 w-3" />
                        Agent frameworks may expose internal systems
                      </p>
                    )}
                  </div>
                )}

                {activeTab === 'keys' && (
                  <div className="space-y-3">
                    {leaks.length > 0 ? (
                      <div className="grid grid-cols-1 gap-2">
                        {leaks.map((leak, i) => (
                          <div key={i} className="flex items-start gap-3 p-2.5 rounded-md bg-red-500/5 border border-red-500/20">
                            <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                            <div className="overflow-hidden">
                              <p className="text-sm font-medium text-red-300 truncate">{leak.key_type || 'Unknown Secret'}</p>
                              <p className="text-xs text-red-400/60 truncate mt-0.5">{leak.repository}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <PositiveEmptyState
                        title="No Exposed Credentials"
                        description="No API keys or secrets found in public repositories — your credential hygiene is solid."
                      />
                    )}
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </Tabs>

        {/* What to Fix First Section */}
        <div className="pt-4 border-t border-gray-800/50 space-y-3">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">What to Fix First</h4>

          {(leaks.length > 0 || agents.length > 0) && (
            <div className="p-3 rounded-lg bg-red-500/5 border border-red-500/20 mb-3">
              <p className="text-sm text-red-300 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
                {leaks.length > 0 ? `${leaks.length} exposed key${leaks.length > 1 ? 's' : ''} detected — rotate immediately` : 'Agent frameworks may expose internal systems'}
              </p>
            </div>
          )}

          {explanation ? (
            <div className="p-3 rounded-lg bg-purple-500/5 border border-purple-500/20">
              <p className="text-sm text-purple-200 leading-relaxed">{explanation}</p>
            </div>
          ) : (
            <p className="text-sm text-gray-400 leading-relaxed">
              {aiSummary ? (aiSummary.length > 200 ? aiSummary.slice(0, 200) + '...' : aiSummary) : "No significant AI footprint detected. Minimal public exposure of AI tooling or credentials."}
            </p>
          )}

          {/* Removed explainError display — we use fallback instead */}

          {scanId && !explanation && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleExplain}
              disabled={isExplaining}
              className="w-full mt-2 bg-purple-600/10 border-purple-500/30 text-purple-300 hover:bg-purple-600/20 hover:border-purple-500/50 hover:text-purple-200 transition-colors"
            >
              {isExplaining ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating explanation...
                </>
              ) : (
                <>
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Explain in simpler words
                </>
              )}
            </Button>
          )}

          {/* Lakera attribution */}
          {hasLakera && (
            <p className="text-xs text-gray-600 flex items-center gap-1.5 pt-2">
              <Shield className="h-3 w-3" />
              Prompt & PII protection powered by Lakera Guard
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyState({ icon: Icon, text }: { icon: any, text: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full py-8 text-center">
      <Icon className="h-8 w-8 text-gray-700 mb-2" />
      <p className="text-sm text-gray-500">{text}</p>
    </div>
  );
}

/**
 * Positive empty state component - Shows a clean security posture message
 * instead of negative "nothing found" messaging.
 */
function PositiveEmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full py-6 text-center">
      <div className="h-10 w-10 rounded-full bg-emerald-500/10 flex items-center justify-center mb-3">
        <ShieldCheck className="h-5 w-5 text-emerald-400" />
      </div>
      <p className="text-sm font-medium text-emerald-400 mb-1">{title}</p>
      <p className="text-xs text-gray-500 max-w-[220px] leading-relaxed">{description}</p>
    </div>
  );
}

export function AIRiskPanelLoading({ scanId }: { scanId: string }) {
  return (
    <Card className="h-full border-gray-800 bg-[#111827]/80 backdrop-blur-sm rounded-2xl shadow-sm flex flex-col justify-center items-center min-h-[400px]">
      <LoadingSpinner size="lg" />
      <p className="text-sm text-gray-500 mt-4 animate-pulse">Analyzing AI footprint...</p>
    </Card>
  );
}

export function AIRiskPanelError() {
  return (
    <Card className="h-full border-red-900/20 bg-red-950/5 backdrop-blur-sm rounded-2xl shadow-sm flex flex-col justify-center items-center min-h-[400px]">
      <AlertTriangle className="h-8 w-8 text-red-500/50 mb-3" />
      <p className="text-sm text-red-400">AI Analysis Failed</p>
    </Card>
  );
}

