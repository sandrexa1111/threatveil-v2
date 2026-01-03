'use client';

import { motion, SVGMotionProps } from 'framer-motion';
import { cn } from '@/lib/utils';

interface IconProps extends SVGMotionProps<SVGSVGElement> {
    className?: string;
}

const iconVariants = {
    initial: { pathLength: 1, opacity: 1 },
    hover: { pathLength: 1, opacity: 1 }
};

// Define variants with proper typing for easing
const pathVariants = {
    initial: { pathLength: 1, strokeDasharray: "1 0" },
    hover: {
        pathLength: [1, 0.8, 1],
        transition: {
            duration: 1.5,
            ease: "easeInOut" as const,
            repeat: Infinity
        }
    }
};

// --- Security / Data Icons (Custom Geometric Style) ---

// "Target" - For specific actions/priorities
export function IconTarget({ className, ...props }: IconProps) {
    return (
        <motion.svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn("w-6 h-6", className)}
            initial="initial"
            whileHover="hover"
            {...props}
        >
            <circle cx="12" cy="12" r="10" className="opacity-30" />
            <motion.circle cx="12" cy="12" r="6" variants={pathVariants} />
            <motion.circle cx="12" cy="12" r="2" />
        </motion.svg>
    );
}

// "Shield" - For protection/trust
export function IconShield({ className, ...props }: IconProps) {
    return (
        <motion.svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn("w-6 h-6", className)}
            initial="initial"
            whileHover="hover"
            {...props}
        >
            <motion.path
                d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
                variants={pathVariants} // Animate the outline
            />
        </motion.svg>
    );
}

// "Brain/Intelligence" - For AI features
export function IconIntelligence({ className, ...props }: IconProps) {
    return (
        <motion.svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn("w-6 h-6", className)}
            initial="initial"
            whileHover="hover"
            {...props}
        >
            <path d="M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" className="opacity-50" />
            <motion.path d="M12 2v2" variants={{ hover: { y: [0, -2, 0] } }} />
            <motion.path d="M12 20v2" variants={{ hover: { y: [0, 2, 0] } }} />
            <motion.path d="M4.93 4.93l1.41 1.41" variants={{ hover: { x: [-2, 0], y: [-2, 0] } }} />
            <motion.path d="M17.66 17.66l1.41 1.41" variants={{ hover: { x: [2, 0], y: [2, 0] } }} />
            <motion.path d="M2 12h2" variants={{ hover: { x: [-2, 0] } }} />
            <motion.path d="M20 12h2" variants={{ hover: { x: [2, 0] } }} />
            <motion.path d="M6.34 17.66l-1.41 1.41" variants={{ hover: { x: [-2, 0], y: [2, 0] } }} />
            <motion.path d="M19.07 4.93l-1.41 1.41" variants={{ hover: { x: [2, 0], y: [-2, 0] } }} />
        </motion.svg>
    );
}

// "Scan/Search" - For visibility
export function IconScan({ className, ...props }: IconProps) {
    return (
        <motion.svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn("w-6 h-6", className)}
            initial="initial"
            whileHover="hover"
            {...props}
        >
            <motion.path d="M2 12h20" className="opacity-20" />
            <motion.path d="M2 12h20"
                initial={{ y: -6, opacity: 0 }}
                animate={{ y: [-6, 6, -6], opacity: [0.2, 0.8, 0.2] }}
                transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                className="text-cyan-400"
            />
            <rect x="2" y="3" width="20" height="18" rx="2" className="opacity-50" />
        </motion.svg>
    );
}

// "Flow/Connect" - For workflow
export function IconFlow({ className, ...props }: IconProps) {
    return (
        <motion.svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn("w-6 h-6", className)}
            initial="initial"
            whileHover="hover"
            {...props}
        >
            <rect x="2" y="6" width="20" height="12" rx="2" className="opacity-30" />
            <motion.path
                d="M2 12h20"
                variants={{ hover: { pathLength: [0, 1], transition: { duration: 0.5 } } }}
            />
            <circle cx="6" cy="12" r="2" />
            <circle cx="18" cy="12" r="2" />
        </motion.svg>
    );
}

// "Lock/Secure" 
export function IconLock({ className, ...props }: IconProps) {
    return (
        <motion.svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn("w-6 h-6", className)}
            initial="initial"
            whileHover="hover"
            {...props}
        >
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <motion.path d="M7 11V7a5 5 0 0 1 10 0v4" variants={{ hover: { y: -2, transition: { repeat: Infinity, repeatType: "reverse", duration: 0.3 } } }} />
        </motion.svg>
    )
}
