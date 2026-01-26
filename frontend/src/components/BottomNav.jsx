import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, PlusCircle, List, Settings } from 'lucide-react';
import clsx from 'clsx';

export default function BottomNav() {
    const navItems = [
        { to: '/', icon: Home, label: 'Home' },
        { to: '/tasks', icon: List, label: 'Tasks' },
        { to: '/create', icon: PlusCircle, label: 'Add' },
        { to: '/settings', icon: Settings, label: 'Settings' },
    ];

    return (
        <div className="absolute bottom-0 left-0 right-0 bg-white border-t border-gray-200 h-16 flex items-center justify-around z-40">
            {navItems.map((item) => (
                <NavLink
                    key={item.label}
                    to={item.to}
                    className={({ isActive }) =>
                        clsx(
                            "flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors",
                            isActive ? "text-blue-600" : "text-gray-400 hover:text-gray-600"
                        )
                    }
                >
                    <item.icon size={24} strokeWidth={2} />
                    <span className="text-xs font-medium">{item.label}</span>
                </NavLink>
            ))}
        </div>
    );
}
