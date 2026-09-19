import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

/** shadcn-style button on the design tokens. Radius 6px (DESIGN_SYSTEM.md §4). */
export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-1.5 rounded-control border font-medium whitespace-nowrap transition-colors disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "border-accent bg-accent text-white hover:bg-accent-bright",
        secondary: "border-border bg-surface-raised text-fg hover:bg-surface-high",
        ghost: "border-transparent bg-transparent text-fg-body hover:bg-surface-raised",
        link: "border-transparent bg-transparent text-accent underline-offset-2 hover:underline",
      },
      size: {
        sm: "h-7 px-2.5 text-[11px]",
        md: "h-8 px-3 text-[12px]",
        lg: "h-10 px-4 text-[13px]",
        icon: "size-8",
      },
    },
    defaultVariants: { variant: "secondary", size: "md" },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, type = "button", ...props }: ButtonProps) {
  return (
    <button type={type} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  );
}
