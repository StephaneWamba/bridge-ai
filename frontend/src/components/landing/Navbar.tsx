"use client";

import Link from "next/link";
import Image from "next/image";
import { ThemeToggle } from "@/components/ThemeToggle";

export function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-[#0A0A0A]/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-3">
            <Image
              src="/logo-full.svg"
              alt="BridgeAI"
              width={120}
              height={40}
              className="dark:invert"
              priority
            />
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-8">
            <Link
              href="#features"
              className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors text-sm font-medium"
            >
              Product
            </Link>
            <Link
              href="#integrations"
              className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors text-sm font-medium"
            >
              Resources
            </Link>
            <Link
              href="#pricing"
              className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors text-sm font-medium"
            >
              Pricing
            </Link>
          </div>

          {/* CTA Button & Theme Toggle */}
          <div className="flex items-center space-x-4">
            <ThemeToggle />
            <Link
              href="/auth/login"
              className="px-4 py-2 text-sm font-medium text-gray-900 dark:text-white hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
            >
              Login
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

