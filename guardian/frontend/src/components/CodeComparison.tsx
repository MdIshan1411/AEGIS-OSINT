import Editor from '@monaco-editor/react';

interface CodeComparisonProps {
  vulnerable: string;
  fixed: string;
  language: string;
}

export function CodeComparison({ vulnerable, fixed, language }: CodeComparisonProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Vulnerable code */}
      <div>
        <h3 className="font-semibold text-red-400 mb-2">❌ Vulnerable Code</h3>
        <div className="bg-slate-800 rounded border border-red-700 overflow-hidden h-[300px]">
          <Editor
            height="100%"
            language={language}
            value={vulnerable}
            options={{ readOnly: true, minimap: { enabled: false } }}
            theme="vs-dark"
          />
        </div>
      </div>

      {/* Fixed code */}
      <div>
        <h3 className="font-semibold text-green-400 mb-2">✅ Fixed Code</h3>
        <div className="bg-slate-800 rounded border border-green-700 overflow-hidden h-[300px]">
          <Editor
            height="100%"
            language={language}
            value={fixed}
            options={{ readOnly: true, minimap: { enabled: false } }}
            theme="vs-dark"
          />
        </div>
      </div>
    </div>
  );
}
