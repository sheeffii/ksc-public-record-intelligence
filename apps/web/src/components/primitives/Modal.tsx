"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { CloseIcon } from "./icons";

export interface ModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  /** 660px palette width (COMPONENTS.md §8) or a narrower dialog. */
  size?: "md" | "palette";
  className?: string;
}

/**
 * Modal over a `--scrim` on a blurred page. 13px radius, heavy shadow plus a
 * 1px accent ring (DESIGN_SYSTEM.md §5). Focus is trapped by Radix.
 */
export function Modal({
  open,
  onOpenChange,
  title,
  description,
  children,
  size = "md",
  className,
}: ModalProps) {
  const t = useTranslations("dialog");
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="bg-scrim fixed inset-0 z-40 backdrop-blur-[2px]" />
        <Dialog.Content
          className={cn(
            "rounded-palette border-border bg-surface shadow-palette ring-accent/60 fixed top-24 left-1/2 z-50 w-[calc(100%-32px)] -translate-x-1/2 border ring-1 focus:outline-none",
            size === "palette" ? "max-w-[660px]" : "max-w-[480px]",
            className,
          )}
        >
          <div className="border-border-subtle flex items-start justify-between gap-3 border-b px-4 py-3">
            <div className="min-w-0">
              <Dialog.Title className="text-fg text-[14px] font-semibold tracking-[-0.01em]">
                {title}
              </Dialog.Title>
              {description ? (
                <Dialog.Description className="text-fg-secondary mt-0.5 text-[11.5px]">
                  {description}
                </Dialog.Description>
              ) : null}
            </div>
            <Dialog.Close
              aria-label={t("close")}
              className="rounded-control text-fg-muted hover:bg-surface-raised hover:text-fg p-1"
            >
              <CloseIcon size={14} />
            </Dialog.Close>
          </div>
          <div className="px-4 py-3">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
