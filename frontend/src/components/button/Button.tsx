interface ButtonProps {
  type?: "submit" | "button";
  className?: string;
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  children: React.ReactNode;
  variant?: "primary" | "secondary";
}

export const Button = ({ type = "button", className = "", onClick, children, variant = "primary", ...rest }: ButtonProps) => {
  return (
    <button
      type={type}
      onClick={onClick}
      className={`button button-${variant} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
};