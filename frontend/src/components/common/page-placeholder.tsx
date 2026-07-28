interface PagePlaceholderProps {
  title: string;
}

export function PagePlaceholder({ title }: PagePlaceholderProps) {
  return (
    <div className="flex flex-1 items-center justify-center">
      <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
    </div>
  );
}
