import { useParams, Link } from "react-router-dom";
import { useAudit } from "../hooks/useAudit";
import { VulnerabilityDetailPanel } from "../components/VulnerabilityDetailPanel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Loader2, GitPullRequest } from "lucide-react";
import { CVESeverityBadge } from "../components/CVESeverityBadge";

export function AuditDetail() {
  const { id } = useParams<{ id: string }>();
  const { data, loading, error } = useAudit(id || "");

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-slate-400">
        <Loader2 className="w-12 h-12 animate-spin mb-4" />
        <p>Loading audit details...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center text-red-400">
        <h2 className="text-xl font-bold mb-2">Error loading audit</h2>
        <p>{error || "Audit not found"}</p>
        <Link to="/" className="text-blue-400 hover:underline mt-4 inline-block">Return to Dashboard</Link>
      </div>
    );
  }

  const { audit, vulnerabilities, dependency_vulnerabilities } = data;
  const isScanning = audit.status === "SCANNING" || audit.status === "QUEUED";

  return (
    <div className="container mx-auto p-6 max-w-7xl animate-in fade-in duration-500">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/">
            <Button variant="ghost" size="icon" className="rounded-full bg-slate-800 text-slate-300 hover:bg-slate-700">
              <ArrowLeft className="w-5 h-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              {audit.repo_owner}/{audit.repo_name}
              {isScanning && <Loader2 className="w-5 h-5 animate-spin text-blue-500" />}
            </h1>
            <p className="text-slate-400 text-sm mt-1">Audit ID: {audit.audit_id}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Badge className={
            audit.status === "COMPLETE" ? "bg-green-600" :
            audit.status === "FAILED" ? "bg-red-600" : "bg-blue-600"
          }>
            {audit.status}
          </Badge>
          {!isScanning && vulnerabilities.some(v => v.suggested_fix) && (
            <Button className="bg-primary hover:bg-primary/90 flex items-center gap-2">
              <GitPullRequest className="w-4 h-4" />
              Create Fix PR
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card className="bg-slate-900 border-red-900/50">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-red-400">Critical</CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold text-red-500">{audit.summary_json.critical || 0}</p></CardContent>
        </Card>
        <Card className="bg-slate-900 border-orange-900/50">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-orange-400">High</CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold text-orange-500">{audit.summary_json.high || 0}</p></CardContent>
        </Card>
        <Card className="bg-slate-900 border-yellow-900/50">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-yellow-400">Medium</CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold text-yellow-500">{audit.summary_json.medium || 0}</p></CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Files Scanned</CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold text-slate-200">{audit.total_files_scanned || 0}</p></CardContent>
        </Card>
      </div>

      <Tabs defaultValue="code" className="w-full">
        <TabsList className="bg-slate-900 border-b border-slate-800 w-full justify-start rounded-none h-auto p-0">
          <TabsTrigger value="code" className="data-[state=active]:bg-slate-800 px-6 py-3 rounded-none">
            Code Findings ({vulnerabilities.length})
          </TabsTrigger>
          <TabsTrigger value="dependencies" className="data-[state=active]:bg-slate-800 px-6 py-3 rounded-none">
            Dependency CVEs ({dependency_vulnerabilities.length})
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="code" className="mt-6 space-y-6">
          {vulnerabilities.length === 0 ? (
            <div className="text-center p-12 bg-slate-900 rounded-lg border border-slate-800">
              <p className="text-slate-400">No code vulnerabilities found in this scan.</p>
            </div>
          ) : (
            vulnerabilities.map(vuln => (
              <VulnerabilityDetailPanel key={vuln.vuln_id} vuln={vuln} />
            ))
          )}
        </TabsContent>

        <TabsContent value="dependencies" className="mt-6">
          {dependency_vulnerabilities.length === 0 ? (
             <div className="text-center p-12 bg-slate-900 rounded-lg border border-slate-800">
             <p className="text-slate-400">No dependency vulnerabilities found in this scan.</p>
           </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {dependency_vulnerabilities.map(dep => (
                <Card key={dep.dep_vuln_id} className="bg-slate-900 border-slate-800">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <CardTitle className="text-lg text-white">{dep.package_name}</CardTitle>
                      <CVESeverityBadge severity={dep.severity} />
                    </div>
                    <p className="text-slate-400 text-sm">{dep.cve_id} (v{dep.current_version})</p>
                  </CardHeader>
                  <CardContent>
                    <p className="text-slate-300 text-sm mb-4 line-clamp-3">{dep.description}</p>
                    <div className="bg-slate-800 p-3 rounded-md text-sm border border-slate-700">
                      <span className="text-green-400 font-semibold block mb-1">Recommendation:</span>
                      <span className="text-slate-200">{dep.recommendation}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
