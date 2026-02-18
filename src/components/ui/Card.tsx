import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

export default function Card({ children, className, onClick }: CardProps) {
  return (
    <div
      className={cn(
        "bg-card border border-border rounded-xl p-5",
        onClick && "cursor-pointer hover:bg-card-hover transition-colors",
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
