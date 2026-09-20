import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { guardianApi } from "../services/api";
import { AuditRecord } from "../types/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Shield, AlertTriangle, CheckCircle, Clock } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function Dashboard() {
  const [audits, setAudits] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAudits = async () => {
      try {
        const data = await guardianApi.getAudits();
        setAudits(data);
      } catch (err) {
        console.error("Failed to fetch audits:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAudits();
  }, []);

  const totalScans = audits.length;
  const totalCritical = audits.reduce((acc, a) => acc + (a.summary_json?.critical || 0), 0);
  const totalHigh = audits.reduce((acc, a) => acc + (a.summary_json?.high || 0), 0);

  return (
    <div className="container mx-auto p-6 max-w-7xl animate-in fade-in duration-500">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-bold text-white flex items-center gap-3">
            <Shield className="w-10 h-10 text-blue-500" />
            GUARDIAN Dashboard
          </h1>
          <p className="text-slate-400 mt-2">AI-Powered Code Security & Dependency Auditor</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">New Audit Scan</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Total Audits</CardTitle>
            <Clock className="w-4 h-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-white">{loading ? "-" : totalScans}</div>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Total Critical Vulns</CardTitle>
            <AlertTriangle className="w-4 h-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-red-500">{loading ? "-" : totalCritical}</div>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Total High Vulns</CardTitle>
            <AlertTriangle className="w-4 h-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-orange-500">{loading ? "-" : totalHigh}</div>
          </CardContent>
        </Card>
      </div>

      <h2 className="text-2xl font-bold text-white mb-4">Recent Audits</h2>
      <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 className="w-8 h-8 animate-spin text-slate-500" />
          </div>
        ) : audits.length === 0 ? (
          <div className="text-center p-12 text-slate-400">
            No audits found. Run `/guardian audit <repo>` in Slack to start.
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-slate-950">
              <TableRow className="border-slate-800 hover:bg-slate-950">
                <TableHead className="text-slate-400">Repository</TableHead>
                <TableHead className="text-slate-400">Status</TableHead>
                <TableHead className="text-slate-400">Date</TableHead>
                <TableHead className="text-slate-400 text-right">Critical / High</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {audits.map((audit) => (
                <TableRow key={audit.audit_id} className="border-slate-800 hover:bg-slate-800/50 cursor-pointer">
                  <TableCell className="font-medium text-blue-400">
                    <Link to={`/audits/${audit.audit_id}`} className="hover:underline">
                      {audit.repo_owner}/{audit.repo_name}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge className={
                      audit.status === "COMPLETE" ? "bg-green-600" :
                      audit.status === "FAILED" ? "bg-red-600" : "bg-blue-600"
                    }>
                      {audit.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-400">
                    {new Date(audit.created_at || audit.started_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="text-red-400 font-bold">{audit.summary_json?.critical || 0}</span>
                    <span className="text-slate-600 mx-2">/</span>
                    <span className="text-orange-400 font-bold">{audit.summary_json?.high || 0}</span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
