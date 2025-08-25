"use client";

import React from "react";

// Minimal, clean logo evoking "weave" (W) with nodes; adapts to theme via currentColor
export default function Logo({ size = 36 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 36 36"
      role="img"
      aria-label="LocalAgentWeaver ロゴ"
      xmlns="http://www.w3.org/2000/svg"
      className="text-foreground"
    >
      {/* Background circle using CSS vars to match theme */}
      <circle cx="18" cy="18" r="18" fill="hsl(var(--muted))" />

      {/* Weave lines */}
      <path
        d="M8 24c4-6 8-6 12 0 4 6 8 6 8 6"
        fill="none"
        stroke="hsl(var(--primary))"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M8 6s4 0 8 6 8 6 12 6"
        fill="none"
        stroke="hsl(var(--primary))"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.9"
      />

      {/* Nodes */}
      <circle cx="8" cy="24" r="1.8" fill="hsl(var(--primary))" />
      <circle cx="20" cy="24" r="1.8" fill="hsl(var(--primary))" />
      <circle cx="32" cy="30" r="1.8" fill="hsl(var(--primary))" />

      <circle cx="8" cy="6" r="1.8" fill="hsl(var(--primary))" />
      <circle cx="16" cy="12" r="1.8" fill="hsl(var(--primary))" />
      <circle cx="32" cy="18" r="1.8" fill="hsl(var(--primary))" />
    </svg>
  );
}
