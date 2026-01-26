import React, { useEffect, useState } from 'react';
import { taskService } from '../services/taskService';

export default function Home() {
    const [stats, setStats] = useState({ total: 0, pending: 0, completed: 0 });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchTasks = async () => {
            try {
                const data = await taskService.getAll();
                setStats({
                    total: data.length,
                    pending: data.filter(t => t.status === 'pending').length,
                    completed: data.filter(t => t.status === 'completed').length
                });
            } catch (error) {
                console.error("Failed to fetch tasks", error);
            } finally {
                setLoading(false);
            }
        };

        fetchTasks();
    }, []);

    return (
        <div className="p-4 space-y-4">
            <h1 className="text-2xl font-bold text-gray-800">Welcome Back</h1>

            <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-600 text-white p-6 rounded-2xl shadow-lg col-span-2">
                    <p className="text-sm opacity-90">Total Tasks</p>
                    <h2 className="text-4xl font-bold mt-1">{loading ? '...' : stats.total}</h2>
                </div>

                <div className="bg-orange-100 text-orange-800 p-4 rounded-xl">
                    <p className="text-xs font-semibold uppercase">Pending</p>
                    <h3 className="text-2xl font-bold">{loading ? '-' : stats.pending}</h3>
                </div>

                <div className="bg-green-100 text-green-800 p-4 rounded-xl">
                    <p className="text-xs font-semibold uppercase">Completed</p>
                    <h3 className="text-2xl font-bold">{loading ? '-' : stats.completed}</h3>
                </div>
            </div>
        </div>
    );
}
