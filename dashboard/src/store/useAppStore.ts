import { create } from "zustand";

interface AppStore {
  selectedFilePath: string | null;
  setSelectedFilePath: (path: string | null) => void;
  editing: boolean;
  setEditing: (v: boolean) => void;
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  activeProject: string | null;
  setActiveProject: (p: string | null) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  selectedFilePath: null,
  setSelectedFilePath: (path) => set({ selectedFilePath: path, editing: false }),
  editing: false,
  setEditing: (v) => set({ editing: v }),
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  activeProject: null,
  setActiveProject: (p) => set({ activeProject: p }),
}));
