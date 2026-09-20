import { useCallback, useEffect } from 'react'
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  Panel,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  BackgroundVariant,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

interface GraphData {
  nodes: any[]
  edges: any[]
}

interface KnowledgeGraphProps {
  graph: GraphData
}

const NODE_COLORS: Record<string, string> = {
  PERSON: '#3b82f6',
  PROFILE: '#8b5cf6',
  ORGANIZATION: '#10b981',
  EMPLOYMENT: '#f59e0b',
  PROJECT: '#ef4444',
  PUBLICATION: '#06b6d4',
  EVENT: '#f97316',
  CONFLICT: '#ef4444',
}

export function KnowledgeGraph({ graph }: KnowledgeGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  useEffect(() => {
    if (!graph?.nodes?.length) return

    const transformedNodes: Node[] = graph.nodes.map((node: any) => {
      const nodeType = (node.node_type || node.type || 'PROFILE').toUpperCase()
      const bgColor = NODE_COLORS[nodeType] || '#64748b'
      const isConflict = nodeType === 'CONFLICT'

      return {
        id: node.id,
        data: { label: node.label || node.id },
        position: node.position || { x: Math.random() * 600, y: Math.random() * 400 },
        style: {
          background: isConflict ? 'transparent' : bgColor,
          color: '#fff',
          padding: '10px 14px',
          borderRadius: isConflict ? '4px' : '10px',
          fontSize: '11px',
          fontWeight: 600,
          letterSpacing: '0.01em',
          width: 'auto',
          minWidth: '100px',
          maxWidth: '160px',
          textAlign: 'center' as const,
          border: isConflict ? `2px dashed ${bgColor}` : `2px solid ${bgColor}`,
          boxShadow: `0 4px 14px ${bgColor}33`,
          cursor: 'pointer',
        },
      }
    })

    const transformedEdges: Edge[] = (graph.edges || []).map((edge: any, index: number) => {
      const isConflict = edge.is_conflict || false

      return {
        id: edge.id || `${edge.source}-${edge.target}-${index}`,
        source: edge.source,
        target: edge.target,
        label: edge.relationship || edge.label,
        animated: !isConflict,
        style: {
          stroke: isConflict ? '#ef4444' : '#475569',
          strokeWidth: isConflict ? 2.5 : 1.5,
          strokeDasharray: isConflict ? '6,4' : '0',
        },
        labelStyle: {
          fill: '#94a3b8',
          fontSize: 10,
          fontWeight: 500,
        },
        labelBgStyle: {
          fill: '#0f172a',
          fillOpacity: 0.85,
        },
      }
    })

    setNodes(transformedNodes)
    setEdges(transformedEdges)
  }, [graph, setNodes, setEdges])

  if (!graph?.nodes?.length) {
    return (
      <div className="w-full h-[500px] bg-slate-800/30 rounded-lg flex items-center justify-center border border-slate-700/30">
        <p className="text-slate-500">No graph data available</p>
      </div>
    )
  }

  return (
    <div className="w-full h-[500px] bg-slate-800/20 rounded-lg overflow-hidden border border-slate-700/30">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        attributionPosition="bottom-left"
      >
        <Background variant={BackgroundVariant.Dots} color="#1e293b" gap={20} size={1} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            return (node.style?.background as string) || '#64748b'
          }}
          style={{ background: '#0f172a' }}
          maskColor="rgba(0,0,0,0.7)"
        />

        {/* Legend */}
        <Panel position="top-left">
          <div className="bg-slate-900/95 backdrop-blur-sm rounded-lg border border-slate-700/50 p-3 space-y-1.5 shadow-xl">
            <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider mb-2">Legend</p>
            {Object.entries(NODE_COLORS).map(([type, color]) => (
              <div key={type} className="flex items-center gap-2 text-xs text-slate-300">
                <div
                  className="w-3 h-3 rounded-sm flex-shrink-0"
                  style={{
                    background: type === 'CONFLICT' ? 'transparent' : color,
                    border: type === 'CONFLICT' ? `2px dashed ${color}` : 'none',
                  }}
                />
                <span className="capitalize">{type.toLowerCase().replace('_', ' ')}</span>
              </div>
            ))}
          </div>
        </Panel>
      </ReactFlow>
    </div>
  )
}
