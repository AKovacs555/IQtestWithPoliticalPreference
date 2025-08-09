import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'

export default function AuthCallback() {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    ;(async () => {
      const { data, error } = await supabase.auth.getSession()
      if (error || !data.session) {
        setError(error?.message ?? 'Authentication failed')
      } else {
        const accessToken = data.session.access_token
        const userId = data.session.user?.id
        if (accessToken) localStorage.setItem('authToken', accessToken)
        if (userId) localStorage.setItem('user_id', userId)
        navigate('/dashboard', { replace: true })
      }
    })()
  }, [navigate])

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div>
          {error}.{' '}
          <a href="/login" className="underline">
            Try again
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen items-center justify-center">
      <div>Loading...</div>
    </div>
  )
}
