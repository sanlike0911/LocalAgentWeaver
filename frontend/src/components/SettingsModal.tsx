"use client";

import React from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useTheme, Theme } from "./ThemeProvider";

interface SettingsModalProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}

export default function SettingsModal({ open, onOpenChange }: SettingsModalProps) {
  const { theme, setTheme } = useTheme();

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTheme(e.target.value as Theme);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent aria-labelledby="settings-title" aria-describedby="settings-desc">
        <DialogHeader>
          <DialogTitle id="settings-title">設定</DialogTitle>
          <DialogDescription id="settings-desc">アプリケーションの外観を設定します。</DialogDescription>
        </DialogHeader>

        <fieldset className="space-y-3" aria-label="テーマ設定">
          <legend className="text-sm font-medium">テーマ</legend>
          <div className="flex items-center space-x-2">
            <input
              id="theme-light"
              type="radio"
              name="theme"
              value="light"
              checked={theme === "light"}
              onChange={onChange}
              className="h-4 w-4"
              aria-checked={theme === "light"}
            />
            <Label htmlFor="theme-light">ライト</Label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              id="theme-dark"
              type="radio"
              name="theme"
              value="dark"
              checked={theme === "dark"}
              onChange={onChange}
              className="h-4 w-4"
              aria-checked={theme === "dark"}
            />
            <Label htmlFor="theme-dark">ダーク</Label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              id="theme-system"
              type="radio"
              name="theme"
              value="system"
              checked={theme === "system"}
              onChange={onChange}
              className="h-4 w-4"
              aria-checked={theme === "system"}
            />
            <Label htmlFor="theme-system">システム設定に合わせる</Label>
          </div>
        </fieldset>
      </DialogContent>
    </Dialog>
  );
}
