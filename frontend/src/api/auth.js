import client from './client'

export const authAPI = {
  login: (studioEmail, password) => {
    return client.post('/auth/login', {
      studio_email: studioEmail,
      password: password,
    })
  },
}
