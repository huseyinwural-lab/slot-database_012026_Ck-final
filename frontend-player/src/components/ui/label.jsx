import * as React from "react"
import { cva } from "class-variance-authority"

function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

const labelVariants = cva(
  "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
)

const Label = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <label
      ref={ref}
      className={cn(labelVariants(), className)}
      {...props}
    />
  )
})
Label.displayName = "Label"

export { Label }
