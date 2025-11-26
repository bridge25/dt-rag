import { cn } from "@/lib/utils"

export function SkeletonCard({ className }: { className?: string }) {
    return (
        <div
            className={cn(
                "relative overflow-hidden rounded-2xl border border-white/5 bg-glass p-6",
                "before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_2s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/5 before:to-transparent",
                className
            )}
        >
            {/* Avatar Skeleton */}
            <div className="mb-6 flex justify-center">
                <div className="h-24 w-24 rounded-full bg-white/5" />
            </div>

            {/* Title & Badge Skeleton */}
            <div className="mb-4 space-y-3">
                <div className="h-6 w-3/4 rounded-lg bg-white/5" />
                <div className="flex gap-2">
                    <div className="h-5 w-16 rounded-full bg-white/5" />
                    <div className="h-5 w-12 rounded-full bg-white/5" />
                </div>
            </div>

            {/* Progress Bar Skeleton */}
            <div className="mb-6 space-y-2">
                <div className="flex justify-between">
                    <div className="h-3 w-12 rounded bg-white/5" />
                    <div className="h-3 w-8 rounded bg-white/5" />
                </div>
                <div className="h-2 w-full rounded-full bg-white/5" />
            </div>

            {/* Stats Grid Skeleton */}
            <div className="grid grid-cols-3 gap-2 border-t border-white/5 pt-4">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="flex flex-col items-center gap-1">
                        <div className="h-5 w-10 rounded bg-white/5" />
                        <div className="h-3 w-8 rounded bg-white/5" />
                    </div>
                ))}
            </div>
        </div>
    )
}
