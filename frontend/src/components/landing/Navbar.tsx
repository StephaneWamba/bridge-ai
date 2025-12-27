"use client";

import Link from "next/link";
import Image from "next/image";

export function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0A0A0A]/80 backdrop-blur-md border-b border-gray-800/50">
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
              className="text-gray-400 hover:text-white transition-colors text-sm font-medium"
            >
              Product
            </Link>
            <Link
              href="#integrations"
              className="text-gray-400 hover:text-white transition-colors text-sm font-medium"
            >
              Resources
            </Link>
            <Link
              href="#pricing"
              className="text-gray-400 hover:text-white transition-colors text-sm font-medium"
            >
              Pricing
            </Link>
          </div>

          {/* CTA Button */}
          <div className="flex items-center space-x-4">
            <Link
              href="/chat"
              className="px-4 py-2 text-sm font-medium text-white hover:text-gray-300 transition-colors"
            >
              Login
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

