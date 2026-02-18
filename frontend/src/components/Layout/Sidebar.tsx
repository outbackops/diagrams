import React from "react";

interface SidebarProps {
  children: React.ReactNode;
}

export const Sidebar: React.FC<SidebarProps> = ({ children }) => {
  return (
    <aside className="flex w-80 flex-col border-r border-gray-200 bg-gray-50">
      {children}
    </aside>
  );
};
