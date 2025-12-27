"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import Image from "next/image";

export function HeroSection() {
  return (
    <section className="relative pt-32 pb-20 sm:pt-40 sm:pb-32 overflow-hidden">
      {/* Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0A0A0A] via-[#0A0A0A] to-[#1A1A1A] -z-10" />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          {/* Main Headline */}
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-white mb-6 tracking-tight">
            BridgeAI
          </h1>

          {/* Subheadline */}
          <p className="text-xl sm:text-2xl lg:text-3xl text-gray-400 mb-8 max-w-3xl mx-auto leading-relaxed">
            Connect your business tools and
            <br />
            automate workflows with AI
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <Link
              href="/chat"
              className="group inline-flex items-center justify-center px-8 py-4 text-base font-medium text-white border border-white/20 rounded-lg hover:border-white/40 hover:bg-white/5 transition-all duration-200"
            >
              Start building
              <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="#features"
              className="inline-flex items-center justify-center px-8 py-4 text-base font-medium text-white/80 hover:text-white transition-colors"
            >
              View demo →
            </Link>
          </div>

          {/* Floating Screenshot */}
          <div className="relative max-w-5xl mx-auto mt-12">
            <div className="relative" style={{ perspective: "1000px" }}>
              {/* Shadow */}
              <div className="absolute inset-0 bg-black/50 blur-3xl rounded-3xl transform translate-y-8 scale-95 -z-10" />
              
              {/* Screenshot Container with 3D Perspective */}
              <div 
                className="relative rounded-2xl border border-gray-800/50 bg-gray-900/50 shadow-2xl overflow-hidden"
                style={{
                  transform: "perspective(1000px) rotateY(-2deg) rotateX(3deg)",
                  transformStyle: "preserve-3d",
                }}
              >
                {/* Placeholder for screenshot - will be replaced with actual image */}
                <div className="aspect-video bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <p className="text-lg font-medium mb-2">Screenshot Placeholder</p>
                    <p className="text-sm">Chat interface screenshot will go here</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

