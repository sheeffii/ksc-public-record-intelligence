"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { CloseIcon } from "./icons";

export type DrawerSide = "left" | "right" | "bottom";

export interface DrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: ReactNode;
  side?: DrawerSide;
  children: ReactNode;
  className?: string;
}

const SIDE_CLASS: Record<DrawerSide, string> = {
  left: "inset-y-0 left-0 w-[min(320px,calc(100%-32px))] border-r",
  right: "inset-y-0 right-0 w-[min(376px,calc(100%-32px))] border-l",
  // Bottom sheet: 16px radius, `--shadow-sheet` (DESIGN_SYSTEM.md §4, §5).
  bottom: "inset-x-0 bottom-0 max-h-[85dvh] rounded-t-sheet border-t shadow-sheet",
};

/**
 * Side panel / bottom sheet. Rails collapse into this below 1280px; on mobile
 * the network inspector uses the bottom variant (HANDOFF.md §5).
 */
export function Drawer({
  open,
  onOpenChange,
  title,
  side = "right",
  children,
  className,
}: DrawerProps) {
  const t = useTranslations("dialog");
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="bg-scrim fixed inset-0 z-40" />
        <Dialog.Content
          data-side={side}
          className={cn(
            "border-border bg-surface fixed z-50 flex flex-col focus:outline-none",
            SIDE_CLASS[side],
            className,
          )}
        >
          <div className="border-border-subtle flex items-center justify-between gap-3 border-b px-3 py-2">
            <Dialog.Title className="text-fg text-[13px] font-semibold">{title}</Dialog.Title>
            <Dialog.Close
              aria-label={t("close")}
              className="rounded-control text-fg-muted hover:bg-surface-raised hover:text-fg p-1"
            >
              <CloseIcon size={14} />
            </Dialog.Close>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto p-3">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
