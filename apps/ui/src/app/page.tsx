import { redirect } from 'next/navigation'

export default function HomePage() {
  // Redirect to taxonomy page as the main entry point
  redirect('/taxonomy')
}