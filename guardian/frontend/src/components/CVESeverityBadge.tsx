import { Badge } from "@/components/ui/badge";

export function CVESeverityBadge({ severity }: { severity: string }) {
  let color = "bg-slate-500";
  if (severity === "CRITICAL") color = "bg-red-600";
  else if (severity === "HIGH") color = "bg-orange-500";
  else if (severity === "MEDIUM") color = "bg-yellow-500";
  else if (severity === "LOW") color = "bg-blue-500";

  return <Badge className={`${color} text-white`}>{severity}</Badge>;
}
