import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import QuestionView from '../views/QuestionView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: HomeView,
        },
        {
            path: '/about/',
            name: 'about',
            // route level code-splitting
            // this generates a separate chunk (About.[hash].js) for this route
            // which is lazy-loaded when the route is visited.
            component: () => import('../views/AboutView.vue')
        },
        {
            path: '/questions/:uuid/',
            name: 'question',
            component: QuestionView,
        },
        {
            path: '/tags/',
            name: 'tags',
            component: HomeView,
        },
        {
            path: '/tags/:slug/',
            name: 'tag',
            component: HomeView,
        },
    ]
})

export default router
