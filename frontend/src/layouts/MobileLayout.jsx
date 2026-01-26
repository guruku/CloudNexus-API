import React from 'react';
import { Outlet } from 'react-router-dom';
import BottomNav from '../components/BottomNav';

export default function MobileLayout() {
    return (
        <div className="min-h-screen bg-gray-100 flex justify-center">
            <div className="w-full max-w-md bg-white min-h-screen shadow-2xl relative flex flex-col">
                {/* Status Bar Simulation (Optional aesthetic) */}
                <div className="h-1 bg-blue-600 w-full sticky top-0 z-50"></div>

                {/* content Area */}
                <main className="flex-1 overflow-y-auto pb-20">
                    <Outlet />
                </main>

                {/* Bottom Navigation */}
                <BottomNav />
            </div>
        </div>
    );
}
