import * as React from "react";

function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

const Button = React.forwardRef(function Button(
  { className, variant = "default", size = "default", type = "button", ...props },
  ref
) {
  const base =
    "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-medium " +
    "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40 " +
    "disabled:pointer-events-none disabled:opacity-50";

  const variants = {
    default: "bg-white text-black hover:bg-white/90",
    secondary: "bg-white/10 text-white hover:bg-white/15 border border-white/15",
    outline: "border border-white/20 bg-transparent text-white hover:bg-white/10",
    ghost: "bg-transparent text-white hover:bg-white/10",
    destructive: "bg-red-600 text-white hover:bg-red-600/90",
    link: "bg-transparent text-white underline-offset-4 hover:underline",
  };

  const sizes = {
    default: "h-10 px-4 py-2",
    sm: "h-9 px-3",
    lg: "h-11 px-6",
    icon: "h-10 w-10",
  };

  return (
    <button
      ref={ref}
      type={type}
      className={cn(base, variants[variant] ?? variants.default, sizes[size] ?? sizes.default, className)}
      {...props}
    />
  );
});
Button.displayName = "Button";

export { Button };
