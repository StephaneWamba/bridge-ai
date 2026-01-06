/** Shimmer loading component for AI processing states. */

import { cn } from "@/lib/utils"

interface ShimmerProps {
  className?: string
  width?: string
  height?: string
}

export function Shimmer({ className, width = "100%", height = "1rem" }: ShimmerProps) {
  return (
    <div
      className={cn("shimmer rounded-md", className)}
      style={{ width, height }}
      aria-label="Loading..."
    />
  )
}

export function ShimmerText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Shimmer
          key={i}
          width={i === lines - 1 ? "80%" : "100%"}
          className="h-4"
        />
      ))}
    </div>
  )
}




