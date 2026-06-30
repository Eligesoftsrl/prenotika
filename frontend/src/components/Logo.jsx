import React from "react";

// Logo Prenotika — glyph "P" geometrico stile moderno UX/UI 2026
// Quadrato arrotondato con cutout circolare che forma una "P" minimalista
export default function Logo({ size = 36, className = "" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Prenotika"
      role="img"
    >
      <defs>
        <linearGradient id="prenotika-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#2C4C3B" />
          <stop offset="100%" stopColor="#3C634D" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="40" height="40" rx="10" fill="url(#prenotika-grad)" />
      {/* "P" stile */}
      <path
        d="M13 10 H22 a8 8 0 0 1 0 16 H17 V31 H13 Z M17 14 V22 H22 a4 4 0 0 0 0 -8 Z"
        fill="#FBF9F6"
      />
      {/* accento arancio */}
      <circle cx="29" cy="13" r="2.5" fill="#D96C4A" />
    </svg>
  );
}
