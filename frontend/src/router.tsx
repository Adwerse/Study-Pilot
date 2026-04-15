import { Navigate, RouterProvider, createBrowserRouter } from 'react-router-dom'
import { Layout } from './components/layout'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { KnowledgePage } from './pages/KnowledgePage'
import { RoadmapPage } from './pages/RoadmapPage'
import { TodayPage } from './pages/TodayPage'

const router = createBrowserRouter([
	{
		path: '/',
		element: <Layout />,
		children: [
			{
				index: true,
				element: <Navigate to="/today" replace />,
			},
			{
				path: 'today',
				element: <TodayPage />,
			},
			{
				path: 'roadmap',
				element: <RoadmapPage />,
			},
			{
				path: 'knowledge',
				element: <KnowledgePage />,
			},
			{
				path: 'analytics',
				element: <AnalyticsPage />,
			},
		],
	},
])

export function AppRouter() {
	return <RouterProvider router={router} />
}
