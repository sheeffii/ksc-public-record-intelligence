/**
 * Inline SVG icons on a 12/14/16/20/24 grid, stroke 1.2–1.8, round caps
 * (DESIGN_SYSTEM.md §9). No icon font, no sprite.
 */

import type { SVGProps } from "react";

export interface IconProps extends SVGProps<SVGSVGElement> {
  size?: 12 | 14 | 16 | 20 | 24;
}

function strokeFor(size: number): number {
  if (size <= 12) return 1.2;
  if (size <= 16) return 1.5;
  return 1.8;
}

function base({ size = 16, ...rest }: IconProps) {
  return {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: strokeFor(size),
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
    focusable: false,
    ...rest,
  };
}

export const SearchIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="11" cy="11" r="7" />
    <path d="m20 20-3.5-3.5" />
  </svg>
);

export const ChevronDownIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="m6 9 6 6 6-6" />
  </svg>
);

export const ArrowRightIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M5 12h14" />
    <path d="m13 6 6 6-6 6" />
  </svg>
);

export const CloseIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M6 6l12 12" />
    <path d="M18 6 6 18" />
  </svg>
);

export const MenuIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M4 7h16" />
    <path d="M4 12h16" />
    <path d="M4 17h16" />
  </svg>
);

/** Verification glyphs — each state has its own glyph (COMPONENTS.md §2). */
export const CheckCircleIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="m8 12.5 2.5 2.5L16 9.5" />
  </svg>
);

export const CrossCircleIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="m9 9 6 6" />
    <path d="m15 9-6 6" />
  </svg>
);

export const AlertCircleIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7.5v5" />
    <path d="M12 16h.01" />
  </svg>
);

export const DashedCircleIcon = (p: IconProps) => (
  <svg {...base(p)} strokeDasharray="3 3">
    <circle cx="12" cy="12" r="9" />
  </svg>
);

export const HomeIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="m4 11 8-7 8 7" />
    <path d="M6 10v10h12V10" />
  </svg>
);

export const NetworkIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="6" cy="6" r="2.5" />
    <circle cx="18" cy="8" r="2.5" />
    <circle cx="12" cy="18" r="2.5" />
    <path d="M8.2 7.2 15.6 8" />
    <path d="m7.5 8 3.4 7.8" />
    <path d="m16.6 10.2-3.5 5.6" />
  </svg>
);

export const DocumentIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M7 3h7l5 5v13H7z" />
    <path d="M14 3v5h5" />
    <path d="M10 13h6" />
    <path d="M10 17h6" />
  </svg>
);

export const SparkIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M12 3v4" />
    <path d="M12 17v4" />
    <path d="M3 12h4" />
    <path d="M17 12h4" />
    <path d="m6 6 2.5 2.5" />
    <path d="m15.5 15.5 2.5 2.5" />
    <path d="m18 6-2.5 2.5" />
    <path d="m8.5 15.5-2.5 2.5" />
  </svg>
);

export const SunIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
  </svg>
);

export const MoonIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" />
  </svg>
);

export const UserIcon = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 20c0-3.5 3.6-6 8-6s8 2.5 8 6" />
  </svg>
);

/** Four-square logo mark (COMPONENTS.md §1 GlobalNav). */
export const LogoMark = (p: IconProps) => (
  <svg {...base(p)} stroke="none" fill="currentColor">
    <rect x="3" y="3" width="8" height="8" rx="1.5" />
    <rect x="13" y="3" width="8" height="8" rx="1.5" opacity="0.7" />
    <rect x="3" y="13" width="8" height="8" rx="1.5" opacity="0.7" />
    <rect x="13" y="13" width="8" height="8" rx="1.5" opacity="0.4" />
  </svg>
);
