import React from "react";

/**
 * Logo Prenotika — usa l'icona ufficiale dal brand kit.
 * size: pixel dimension del logo quadrato.
 * variant: "icon" (solo simbolo, da usare in sidebar/avatar) | "mark" (svg vettoriale stilizzato, fallback senza asset).
 */
export default function Logo({ size = 36, className = "", variant = "icon" }) {
  if (variant === "icon") {
    return (
      <img
        src="/prenotika-icon.png"
        alt="Prenotika"
        width={size}
        height={size}
        className={className}
        style={{ width: size, height: size, objectFit: "contain" }}
      />
    );
  }
  // Vector fallback (Sora-style "P" with gradient identity)
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Prenotika"
      role="img"
    >
      <defs>
        <linearGradient id="prenotika-brand-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#7C3AED" />
          <stop offset="55%" stopColor="#60A5FA" />
          <stop offset="100%" stopColor="#2DD4BF" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="44" height="44" rx="12" fill="url(#prenotika-brand-grad)" />
      <path d="M16 12 H27 a9 9 0 0 1 0 18 H21 V37 H16 Z M21 17 V25 H27 a4 4 0 0 0 0 -8 Z" fill="#FFFFFF" />
      <circle cx="34" cy="33" r="3" fill="#2DD4BF" />
    </svg>
  );
}
