'use client';

import { motion, HTMLMotionProps, Variants } from 'framer-motion';
import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

// --- Types ---

interface FadeInProps extends HTMLMotionProps<'div'> {
    delay?: number;
    duration?: number;
    yOffset?: number;
    direction?: 'up' | 'down' | 'left' | 'right';
    viewportOnce?: boolean;
}

interface StaggerContainerProps extends HTMLMotionProps<'div'> {
    delay?: number;
    staggerDelay?: number;
    viewportOnce?: boolean;
}

// --- Variants ---

const fadeInVariants = (yOffset: number, direction: string): Variants => {
    let initialX = 0;
    let initialY = 0;

    switch (direction) {
        case 'up': initialY = yOffset; break;
        case 'down': initialY = -yOffset; break;
        case 'left': initialX = yOffset; break;
        case 'right': initialX = -yOffset; break;
        case 'none': break;
    }

    return {
        hidden: { opacity: 0, x: initialX, y: initialY },
        visible: {
            opacity: 1,
            x: 0,
            y: 0,
            transition: { type: 'spring', stiffness: 50, damping: 20 }
        },
    };
};

const staggerVariants = (staggerDelay: number = 0.1, delay: number = 0): Variants => ({
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            delayChildren: delay,
            staggerChildren: staggerDelay,
        },
    },
});

// --- Components ---

export function FadeIn({
    children,
    delay = 0,
    duration = 0.5,
    yOffset = 20,
    direction = 'up',
    viewportOnce = true,
    className,
    ...props
}: FadeInProps) {
    return (
        <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: viewportOnce, margin: "-50px" }}
            transition={{ duration, delay, ease: "easeOut" }}
            variants={fadeInVariants(yOffset, direction)}
            className={className}
            {...props}
        >
            {children}
        </motion.div>
    );
}

export function StaggerContainer({
    children,
    delay = 0,
    staggerDelay = 0.1,
    viewportOnce = true,
    className,
    ...props
}: StaggerContainerProps) {
    return (
        <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: viewportOnce, margin: "-50px" }}
            variants={staggerVariants(staggerDelay, delay)}
            className={className}
            {...props}
        >
            {children}
        </motion.div>
    );
}

// --- Specialized Effects ---

export function GlowEffect({ className }: { className?: string }) {
    return (
        <div className={cn("absolute inset-0 -z-10 opacity-0 transition-opacity duration-500 group-hover:opacity-100", className)}>
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-cyan-500/10 blur-xl opacity-50" />
        </div>
    );
}

export function AmbientBackground() {
    return (
        <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
            <div className="absolute top-[-20%] left-[-10%] w-[70vw] h-[70vw] bg-purple-900/5 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow" />
            <div className="absolute bottom-[-20%] right-[-10%] w-[70vw] h-[70vw] bg-cyan-900/5 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow" style={{ animationDelay: '2s' }} />
            <div className="absolute inset-0 bg-[url('/noise.svg')] opacity-[0.02] mix-blend-overlay" />
        </div>
    );
}

export function AnimatedNumber({ value }: { value: number }) {
    // Simple implementation for now, can be expanded with Framer Motion useSpring
    return <span>{value}</span>;
}

export const SmoothTransition = {
    type: "spring",
    stiffness: 70,
    damping: 20
};
