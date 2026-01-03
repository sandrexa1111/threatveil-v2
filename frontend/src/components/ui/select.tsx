"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { ChevronDown } from "lucide-react"

interface SelectContextValue {
    value: string
    onValueChange: (value: string) => void
    open: boolean
    setOpen: (open: boolean) => void
}

const SelectContext = React.createContext<SelectContextValue | null>(null)

function useSelectContext() {
    const context = React.useContext(SelectContext)
    if (!context) {
        throw new Error("Select components must be used within a Select")
    }
    return context
}

interface SelectProps {
    value?: string
    defaultValue?: string
    onValueChange?: (value: string) => void
    disabled?: boolean
    children: React.ReactNode
}

const Select = React.forwardRef<HTMLDivElement, SelectProps>(
    ({ value, defaultValue, onValueChange, disabled, children }, ref) => {
        const [internalValue, setInternalValue] = React.useState(defaultValue || "")
        const [open, setOpen] = React.useState(false)

        const currentValue = value !== undefined ? value : internalValue
        const handleValueChange = (newValue: string) => {
            if (value === undefined) {
                setInternalValue(newValue)
            }
            onValueChange?.(newValue)
            setOpen(false)
        }

        return (
            <SelectContext.Provider
                value={{
                    value: currentValue,
                    onValueChange: handleValueChange,
                    open,
                    setOpen,
                }}
            >
                <div ref={ref} className="relative" data-disabled={disabled}>
                    {children}
                </div>
            </SelectContext.Provider>
        )
    }
)
Select.displayName = "Select"

interface SelectTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children: React.ReactNode
}

const SelectTrigger = React.forwardRef<HTMLButtonElement, SelectTriggerProps>(
    ({ className, children, ...props }, ref) => {
        const { open, setOpen } = useSelectContext()

        return (
            <button
                ref={ref}
                type="button"
                onClick={() => setOpen(!open)}
                className={cn(
                    "flex h-10 w-full items-center justify-between rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
                    className
                )}
                {...props}
            >
                {children}
                <ChevronDown className="h-4 w-4 opacity-50" />
            </button>
        )
    }
)
SelectTrigger.displayName = "SelectTrigger"

interface SelectValueProps {
    placeholder?: string
}

const SelectValue = React.forwardRef<HTMLSpanElement, SelectValueProps>(
    ({ placeholder }, ref) => {
        const { value } = useSelectContext()

        return (
            <span ref={ref} className={!value ? "text-slate-500" : ""}>
                {value || placeholder}
            </span>
        )
    }
)
SelectValue.displayName = "SelectValue"

interface SelectContentProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode
}

const SelectContent = React.forwardRef<HTMLDivElement, SelectContentProps>(
    ({ className, children, ...props }, ref) => {
        const { open } = useSelectContext()

        if (!open) return null

        return (
            <div
                ref={ref}
                className={cn(
                    "absolute z-50 min-w-[8rem] overflow-hidden rounded-md border border-slate-700 bg-slate-800 text-white shadow-md animate-in fade-in-0 zoom-in-95 top-full mt-1 w-full",
                    className
                )}
                {...props}
            >
                <div className="p-1">{children}</div>
            </div>
        )
    }
)
SelectContent.displayName = "SelectContent"

interface SelectItemProps extends React.HTMLAttributes<HTMLDivElement> {
    value: string
    children: React.ReactNode
}

const SelectItem = React.forwardRef<HTMLDivElement, SelectItemProps>(
    ({ className, value, children, ...props }, ref) => {
        const { value: selectedValue, onValueChange } = useSelectContext()
        const isSelected = selectedValue === value

        return (
            <div
                ref={ref}
                className={cn(
                    "relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 px-2 text-sm outline-none transition-colors",
                    isSelected ? "bg-slate-700 text-white" : "hover:bg-slate-700/50",
                    className
                )}
                onClick={() => onValueChange(value)}
                {...props}
            >
                {children}
            </div>
        )
    }
)
SelectItem.displayName = "SelectItem"

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem }
