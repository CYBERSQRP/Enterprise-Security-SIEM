/**
 * Advanced Visualization Components for SIEM
 *
 * This module provides advanced visualization components including:
 * - Attack flow visualization
 * - 3D network topology
 * - Real-time threat map
 * - Interactive investigation graphs
 */

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import * as THREE from 'three';

// ============================================================================
// Attack Flow Visualization Component
// ============================================================================

interface AttackNode {
  id: string;
  type: 'initial_access' | 'execution' | 'persistence' | 'privilege_escalation' |
        'defense_evasion' | 'credential_access' | 'discovery' | 'lateral_movement' |
        'collection' | 'exfiltration' | 'command_control';
  technique: string;
  timestamp: Date;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
}

interface AttackEdge {
  source: string;
  target: string;
  confidence: number;
}

interface AttackFlowVisualizationProps {
  nodes: AttackNode[];
  edges: AttackEdge[];
  onNodeClick?: (node: AttackNode) => void;
}

export const AttackFlowVisualization: React.FC<AttackFlowVisualizationProps> = ({
  nodes,
  edges,
  onNodeClick
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const width = 1200;
    const height = 800;

    svg.selectAll('*').remove();

    const g = svg.append('g');

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Define arrow markers
    svg.append('defs').selectAll('marker')
      .data(['end'])
      .join('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#999');

    // Color scale for severity
    const severityColor = d3.scaleOrdinal<string>()
      .domain(['low', 'medium', 'high', 'critical'])
      .range(['#4CAF50', '#FFC107', '#FF9800', '#F44336']);

    // Create force simulation
    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(edges)
        .id((d: any) => d.id)
        .distance(150))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    // Draw edges
    const links = g.append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', (d) => d.confidence)
      .attr('stroke-width', 2)
      .attr('marker-end', 'url(#arrow)');

    // Draw nodes
    const nodeGroups = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .on('click', (event, d) => {
        if (onNodeClick) onNodeClick(d);
      });

    nodeGroups.append('circle')
      .attr('r', 20)
      .attr('fill', (d) => severityColor(d.severity))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    nodeGroups.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 35)
      .attr('font-size', '12px')
      .text((d) => d.technique.substring(0, 20));

    // Update positions on tick
    simulation.on('tick', () => {
      links
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      nodeGroups.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // Drag behavior
    const drag = d3.drag<any, any>()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    nodeGroups.call(drag);

  }, [nodes, edges, onNodeClick]);

  return (
    <div className="attack-flow-visualization">
      <svg ref={svgRef} width="100%" height="800" />
    </div>
  );
};

// ============================================================================
// 3D Network Topology Visualization
// ============================================================================

interface NetworkNode {
  id: string;
  type: 'server' | 'workstation' | 'router' | 'firewall' | 'switch';
  label: string;
  risk_score: number;
  position?: [number, number, number];
}

interface NetworkConnection {
  source: string;
  target: string;
  traffic_volume: number;
  is_suspicious: boolean;
}

interface NetworkTopology3DProps {
  nodes: NetworkNode[];
  connections: NetworkConnection[];
}

export const NetworkTopology3D: React.FC<NetworkTopology3DProps> = ({
  nodes,
  connections
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = 600;

    // Create scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0a);

    // Create camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = 500;

    // Create renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    containerRef.current.appendChild(renderer.domElement);

    // Add lights
    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight.position.set(1, 1, 1);
    scene.add(directionalLight);

    // Create nodes
    const nodeObjects: Map<string, THREE.Mesh> = new Map();

    nodes.forEach((node) => {
      const geometry = new THREE.SphereGeometry(10, 32, 32);

      // Color based on risk score
      const color = new THREE.Color();
      color.setHSL((1 - node.risk_score) * 0.3, 1, 0.5);

      const material = new THREE.MeshPhongMaterial({ color });
      const sphere = new THREE.Mesh(geometry, material);

      // Position nodes in 3D space
      const position = node.position || [
        Math.random() * 400 - 200,
        Math.random() * 400 - 200,
        Math.random() * 400 - 200
      ];
      sphere.position.set(...position);

      scene.add(sphere);
      nodeObjects.set(node.id, sphere);

      // Add label
      // (In production, use THREE.CSS2DRenderer for labels)
    });

    // Create connections
    connections.forEach((conn) => {
      const sourceNode = nodeObjects.get(conn.source);
      const targetNode = nodeObjects.get(conn.target);

      if (sourceNode && targetNode) {
        const material = new THREE.LineBasicMaterial({
          color: conn.is_suspicious ? 0xff0000 : 0x00ff00,
          opacity: 0.6,
          transparent: true
        });

        const points = [sourceNode.position, targetNode.position];
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const line = new THREE.Line(geometry, material);

        scene.add(line);
      }
    });

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);

      // Rotate scene slowly
      scene.rotation.y += 0.001;

      renderer.render(scene, camera);
    };

    animate();

    // Cleanup
    return () => {
      containerRef.current?.removeChild(renderer.domElement);
    };
  }, [nodes, connections]);

  return <div ref={containerRef} className="network-topology-3d" />;
};

// ============================================================================
// Real-time Threat Map
// ============================================================================

interface ThreatEvent {
  id: string;
  source_location: [number, number]; // [lat, lng]
  target_location: [number, number];
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: string;
  timestamp: Date;
}

interface ThreatMapProps {
  threats: ThreatEvent[];
}

export const ThreatMap: React.FC<ThreatMapProps> = ({ threats }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width = 1200;
    const height = canvas.height = 600;

    // Simple world map projection (Mercator-like)
    const project = (lat: number, lng: number): [number, number] => {
      const x = (lng + 180) * (width / 360);
      const y = (90 - lat) * (height / 180);
      return [x, y];
    };

    // Clear canvas
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, width, height);

    // Draw simplified world map
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    // (In production, use actual map data or map library)

    // Draw grid
    ctx.beginPath();
    for (let i = 0; i <= 360; i += 30) {
      const x = (i * width) / 360;
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
    }
    for (let i = 0; i <= 180; i += 30) {
      const y = (i * height) / 180;
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
    }
    ctx.stroke();

    // Draw threats
    threats.forEach((threat) => {
      const [sx, sy] = project(...threat.source_location);
      const [tx, ty] = project(...threat.target_location);

      // Draw arc from source to target
      const severityColors = {
        low: '#4CAF50',
        medium: '#FFC107',
        high: '#FF9800',
        critical: '#F44336'
      };

      ctx.strokeStyle = severityColors[threat.severity];
      ctx.lineWidth = 2;
      ctx.globalAlpha = 0.6;

      ctx.beginPath();
      ctx.moveTo(sx, sy);

      // Quadratic curve for arc effect
      const cx = (sx + tx) / 2;
      const cy = Math.min(sy, ty) - 100;
      ctx.quadraticCurveTo(cx, cy, tx, ty);
      ctx.stroke();

      // Draw dots at endpoints
      ctx.fillStyle = severityColors[threat.severity];
      ctx.globalAlpha = 1.0;
      ctx.beginPath();
      ctx.arc(sx, sy, 4, 0, 2 * Math.PI);
      ctx.fill();

      ctx.beginPath();
      ctx.arc(tx, ty, 4, 0, 2 * Math.PI);
      ctx.fill();
    });

  }, [threats]);

  return (
    <div className="threat-map">
      <canvas ref={canvasRef} />
    </div>
  );
};

// ============================================================================
// Interactive Investigation Graph
// ============================================================================

interface InvestigationNode {
  id: string;
  type: 'user' | 'ip' | 'host' | 'file' | 'process' | 'domain';
  label: string;
  metadata: Record<string, any>;
}

interface InvestigationEdge {
  source: string;
  target: string;
  relationship: string;
}

interface InvestigationGraphProps {
  nodes: InvestigationNode[];
  edges: InvestigationEdge[];
  onNodeExpand?: (nodeId: string) => void;
}

export const InvestigationGraph: React.FC<InvestigationGraphProps> = ({
  nodes,
  edges,
  onNodeExpand
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const width = 1200;
    const height = 800;

    svg.selectAll('*').remove();

    const g = svg.append('g');

    // Zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Node type colors
    const nodeColors: Record<string, string> = {
      user: '#2196F3',
      ip: '#F44336',
      host: '#4CAF50',
      file: '#FF9800',
      process: '#9C27B0',
      domain: '#00BCD4'
    };

    // Force simulation
    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(edges)
        .id((d: any) => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-500))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // Draw edges
    const links = g.append('g')
      .selectAll('path')
      .data(edges)
      .join('path')
      .attr('stroke', '#999')
      .attr('stroke-width', 1.5)
      .attr('fill', 'none');

    // Draw edge labels
    const edgeLabels = g.append('g')
      .selectAll('text')
      .data(edges)
      .join('text')
      .attr('font-size', '10px')
      .attr('fill', '#999')
      .text((d) => d.relationship);

    // Draw nodes
    const nodeGroups = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .on('dblclick', (event, d) => {
        if (onNodeExpand) onNodeExpand(d.id);
      });

    nodeGroups.append('circle')
      .attr('r', 15)
      .attr('fill', (d) => nodeColors[d.type] || '#999')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    // Add icon/text for node type
    nodeGroups.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 4)
      .attr('fill', '#fff')
      .attr('font-size', '12px')
      .text((d) => d.type[0].toUpperCase());

    nodeGroups.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 30)
      .attr('font-size', '11px')
      .text((d) => d.label);

    // Update positions
    simulation.on('tick', () => {
      links.attr('d', (d: any) => {
        const dx = d.target.x - d.source.x;
        const dy = d.target.y - d.source.y;
        const dr = Math.sqrt(dx * dx + dy * dy);
        return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
      });

      edgeLabels
        .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
        .attr('y', (d: any) => (d.source.y + d.target.y) / 2);

      nodeGroups.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // Drag behavior
    const drag = d3.drag<any, any>()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    nodeGroups.call(drag);

  }, [nodes, edges, onNodeExpand]);

  return (
    <div className="investigation-graph">
      <svg ref={svgRef} width="100%" height="800" />
    </div>
  );
};

// Export all components
export default {
  AttackFlowVisualization,
  NetworkTopology3D,
  ThreatMap,
  InvestigationGraph
};
