import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import HomeView from '../views/HomeView.vue'
import CategoryView from '../views/CategoryView.vue'
import PostView from '../views/PostView.vue'
import WriteView from '../views/WriteView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import DailyView from '../views/DailyView.vue'
import MomentsView from '../views/MomentsView.vue'
import ClubView from '../views/ClubView.vue'
import ProfileView from '../views/ProfileView.vue'
import NotificationsView from '../views/NotificationsView.vue'
import AdminView from '../views/AdminView.vue'
import ContactView from '../views/ContactView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/c/:slug', name: 'category', component: CategoryView },
    { path: '/posts/:id', name: 'post', component: PostView },
    { path: '/write', name: 'write', component: WriteView, meta: { auth: true } },
    { path: '/daily', name: 'daily', component: DailyView },
    { path: '/moments', name: 'moments', component: MomentsView },
    { path: '/club', name: 'club', component: ClubView },
    { path: '/contact', name: 'contact', component: ContactView },
    { path: '/profile', name: 'profile', component: ProfileView, meta: { auth: true } },
    { path: '/notifications', name: 'notifications', component: NotificationsView, meta: { auth: true } },
    { path: '/admin', name: 'admin', component: AdminView, meta: { auth: true, admin: true } },
    { path: '/login', name: 'login', component: LoginView },
    { path: '/forgot-password', name: 'forgot-password', component: ForgotPasswordView },
    { path: '/register', name: 'register', component: RegisterView },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.auth && !auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.admin && !auth.isAdmin) {
    return { name: 'home' }
  }
  return true
})

export default router
