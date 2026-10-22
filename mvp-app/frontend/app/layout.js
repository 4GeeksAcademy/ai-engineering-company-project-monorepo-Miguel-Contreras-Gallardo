import "./globals.css";

export const metadata = {
  title: "MVP en marcha",
  description: "TrackFlow MVP — verificando conectividad con el backend",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}