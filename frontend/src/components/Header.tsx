"use client";

import React, { useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useParams } from "next/navigation";
import { Settings, LogOut, Menu } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import SettingsModal from "./SettingsModal";
import Logo from "./Logo";
import { projectApi } from "@/utils/api";

export default function Header() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useParams();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [projectName, setProjectName] = useState<string>("");
  const menuRef = useRef<HTMLDivElement | null>(null);

  // Close on outside click
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  // fetch project name when projectId is present (e.g., chat page)
  useEffect(() => {
    const projectId = params?.projectId as string | undefined;
    if (!projectId) {
      setProjectName("");
      return;
    }
    (async () => {
      try {
        const res = await projectApi.getProject(projectId);
        setProjectName(res.data?.name ?? "");
      } catch {
        setProjectName("");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params?.projectId]);

  // Hide header on auth pages
  if (pathname?.startsWith("/auth")) return null;

  const initials = user?.username?.slice(0, 2).toUpperCase() || "U";

  return (
    <header role="banner" className="sticky top-0 z-30 bg-background border-b">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 bg-primary text-primary-foreground px-3 py-1 rounded">
        メインコンテンツへスキップ
      </a>
      <div className="mx-auto w-full pl-[20px] pr-5 flex h-14 items-center justify-between">
        <button
          aria-label="ホームに戻る"
          className="font-semibold text-sm md:text-base"
          onClick={() => router.push("/dashboard")}
        >
          <Logo size={36} />
          <span
            className="ml-3 hidden sm:inline-block font-medium truncate max-w-[50vw]"
            title={projectName || "LocalAgentWeaver"}
          >
            {projectName || "LocalAgentWeaver"}
          </span>
        </button>

        <div className="flex items-center gap-2">
          {/* Mobile menu placeholder for future (e.g., toggling side panels) */}
          <button
            type="button"
            className="inline-flex md:hidden items-center justify-center rounded-md p-2 hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
            aria-label="メニュー"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="relative" ref={menuRef}>
            <button
              type="button"
              aria-haspopup="menu"
              aria-expanded={open}
              onClick={() => setOpen((v) => !v)}
              className="inline-flex items-center justify-center h-9 w-9 rounded-full bg-muted text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <span aria-hidden className="text-xs font-medium">{initials}</span>
              <span className="sr-only">ユーザーメニューを開く</span>
            </button>

            {open && (
              <div
                role="menu"
                aria-label="ユーザーメニュー"
                className="absolute right-0 mt-2 w-56 rounded-md border bg-popover text-popover-foreground shadow-md focus:outline-none"
              >
                <button
                  role="menuitem"
                  className="w-full text-left px-3 py-2 hover:bg-muted focus:bg-muted focus:outline-none"
                  onClick={() => {
                    setSettingsOpen(true);
                    setOpen(false);
                  }}
                >
                  <div className="flex items-center gap-2">
                    <Settings className="h-4 w-4" />
                    設定
                  </div>
                </button>
                <button
                  role="menuitem"
                  className="w-full text-left px-3 py-2 text-red-600 hover:bg-muted focus:bg-muted focus:outline-none"
                  onClick={() => {
                    setOpen(false);
                    if (window.confirm("ログアウトしますか？")) {
                      logout();
                    }
                  }}
                >
                  <div className="flex items-center gap-2">
                    <LogOut className="h-4 w-4" />
                    ログアウト
                  </div>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <SettingsModal open={settingsOpen} onOpenChange={setSettingsOpen} />
    </header>
  );
}
