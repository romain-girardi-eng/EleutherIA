import React from 'react';
import { cn } from "@/lib/utils";
import { motion, type Variants } from 'framer-motion';

// Icon component for contact details
const InfoIcon = ({ type }: { type: 'website' | 'phone' | 'address' | 'doi' | 'github' | 'email' }) => {
    const icons = {
        website: (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 text-primary">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="2" x2="22" y1="12" y2="12"></line>
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
            </svg>
        ),
        phone: (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 text-primary">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
            </svg>
        ),
        address: (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 text-primary">
                <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path>
                <circle cx="12" cy="10" r="3"></circle>
            </svg>
        ),
        doi: (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 text-primary">
                <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"></path>
            </svg>
        ),
        github: (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 text-primary">
                <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"></path>
                <path d="M9 18c-4.51 2-5-2-7-2"></path>
            </svg>
        ),
        email: (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 text-primary">
                <rect width="20" height="16" x="2" y="4" rx="2"></rect>
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
            </svg>
        ),
    };
    return <div className="mr-1.5 flex-shrink-0 [&_svg]:h-3.5 [&_svg]:w-3.5 sm:[&_svg]:h-4 sm:[&_svg]:w-4">{icons[type]}</div>;
};


// Prop types for the HeroSection component
interface HeroSectionProps {
  className?: string;
  logo?: {
    url: string;
    alt: string;
    text?: string;
  };
  slogan?: string;
  title: React.ReactNode;
  subtitle: string;
  callToAction: {
    text: string;
    href: string;
  };
  ctaArea?: React.ReactNode;
  backgroundImage?: string;
  backgroundComponent?: React.ReactNode;
  contactInfo: {
    type: 'website' | 'phone' | 'address' | 'doi' | 'github' | 'email';
    label: string;
    href?: string;
  }[];
}

const HeroSection = React.forwardRef<HTMLDivElement, HeroSectionProps>(
  ({ className, logo, slogan, title, subtitle, callToAction, ctaArea, backgroundImage, backgroundComponent, contactInfo }, ref) => {

    // Animation variants for the container to orchestrate children animations
    const containerVariants: Variants = {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: 0.15,
          delayChildren: 0.2,
        },
      },
    };

    // Animation variants for individual text/UI elements
    const itemVariants: Variants = {
      hidden: { y: 20, opacity: 0 },
      visible: {
        y: 0,
        opacity: 1,
        transition: {
          duration: 0.5,
          ease: "easeOut" as const,
        },
      },
    };

    return (
      <motion.section
        ref={ref}
        className={cn(
          "relative overflow-hidden m-0 p-0 bg-white",
          className
        )}
        style={{
          height: '100dvh',
          marginTop: 0,
        }}
        initial="hidden"
        animate="visible"
        variants={containerVariants}
      >

        {/* ── Single background — rendered ONCE, never display:none ────────── */}
        {/* Mobile: left-0 → full-screen canvas, particles center at 50%.      */}
        {/* Desktop: md:left-1/2 → right-half canvas, particles center at 75%. */}
        {backgroundComponent ? (
          <div className="absolute top-0 bottom-0 left-0 right-0 md:left-1/2 bg-zinc-950">
            {backgroundComponent}
          </div>
        ) : backgroundImage ? (
          <div
            className="absolute top-0 bottom-0 left-0 right-0 md:left-1/2"
            style={{ backgroundImage: `url(${backgroundImage})`, backgroundSize: 'cover', backgroundPosition: 'center' }}
          />
        ) : (
          <div className="absolute inset-0 bg-zinc-950" />
        )}

        {/* ── MOBILE layout — two stacked bands, matches desktop's
             parchment/cosmic dichotomy without smothering the particle
             canvas in a dark scrim ───────────────────────────────────────── */}
        <div className="md:hidden absolute inset-0 z-[5] flex flex-col overflow-hidden">

          {/* TOP — cosmic constellation panel (~38%) */}
          <div className="relative flex-shrink-0" style={{ height: '38%' }}>
            {/* Tiny scrim at the very top so the logo reads cleanly without
                fighting the particles. */}
            <div
              aria-hidden="true"
              className="absolute inset-x-0 top-0 h-24 pointer-events-none"
              style={{ background: 'linear-gradient(to bottom, rgba(2,6,23,0.55) 0%, transparent 100%)' }}
            />
            {logo && (
              <motion.div
                variants={itemVariants}
                className="absolute top-4 left-5 z-20 flex items-center gap-2"
              >
                <img
                  src={logo.url}
                  alt={logo.alt}
                  className="h-9 brightness-0 invert opacity-90"
                />
                <span className="font-display text-[11px] font-semibold uppercase tracking-[0.18em] text-white/70">
                  EleutherIA
                </span>
              </motion.div>
            )}
            {/* Soft fade at the bottom of the cosmic band so it meets the
                parchment without a hard seam. */}
            <div
              aria-hidden="true"
              className="absolute inset-x-0 bottom-0 h-16 pointer-events-none"
              style={{ background: 'linear-gradient(to bottom, transparent 0%, #fdfbf7 100%)' }}
            />
          </div>

          {/* BOTTOM — parchment scholarly panel (~62%) */}
          <motion.div
            variants={containerVariants}
            className="relative flex-1 min-h-0 overflow-hidden"
            style={{
              background:
                'linear-gradient(180deg, #fdfbf7 0%, #faf7f2 55%, #f5efe2 100%)',
            }}
          >
            {/* Faint paper dot grid, scholarly cue (same as desktop) */}
            <div
              aria-hidden="true"
              className="absolute inset-0 pointer-events-none"
              style={{
                backgroundImage:
                  'radial-gradient(circle, rgba(160,140,110,0.10) 1px, transparent 1px)',
                backgroundSize: '28px 28px',
                maskImage:
                  'radial-gradient(ellipse 95% 70% at 50% 30%, black 30%, transparent 75%)',
                WebkitMaskImage:
                  'radial-gradient(ellipse 95% 70% at 50% 30%, black 30%, transparent 75%)',
              }}
            />

            <div className="relative h-full flex flex-col px-6 pt-6 pb-5 overflow-y-auto">
              <motion.h1
                variants={itemVariants}
                className="font-display text-[26px] leading-[1.1] font-semibold tracking-tight text-stone-900"
              >
                {title}
              </motion.h1>
              {slogan && (
                <motion.p
                  variants={itemVariants}
                  className="mt-2 text-[13px] leading-snug text-stone-600"
                >
                  {slogan}
                </motion.p>
              )}
              <motion.p
                variants={itemVariants}
                className="mt-1.5 text-[12.5px] leading-relaxed text-stone-500/90"
              >
                {subtitle}
              </motion.p>

              {/* CTA codex — reuses the warm hover palette from desktop */}
              {ctaArea ? (
                <motion.div
                  variants={itemVariants}
                  className="mt-4 -mx-2"
                  data-mobile-cta-area
                >
                  {ctaArea}
                </motion.div>
              ) : (
                <motion.a
                  variants={itemVariants}
                  href={callToAction.href}
                  className="mt-4 inline-flex items-center gap-1.5 self-start text-[11px] font-bold tracking-[0.18em] uppercase text-amber-700 hover:text-amber-800 transition-colors"
                >
                  {callToAction.text}
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14"></path>
                    <path d="m12 5 7 7-7 7"></path>
                  </svg>
                </motion.a>
              )}

              <div className="flex-1" />

              {/* Footer info — restrained, same metadata strip as desktop */}
              <motion.div
                variants={itemVariants}
                className="mt-4 pt-3 border-t border-stone-200/70 flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-stone-500"
              >
                {contactInfo.map((info, index) => (
                  <div key={index} className="inline-flex items-center gap-1">
                    <InfoIcon type={info.type} />
                    {info.href ? (
                      <a
                        href={info.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-amber-700 transition-colors"
                      >
                        {info.label}
                      </a>
                    ) : (
                      <span>{info.label}</span>
                    )}
                  </div>
                ))}
              </motion.div>
            </div>
          </motion.div>
        </div>

        {/* ── DESKTOP panel — diagonal clip, warm living surface ───────────── */}
        {/* 55% wide: 100%=55% screen at top, 90.91%=50% screen at bottom.    */}
        <div
          className="hidden md:flex absolute inset-y-0 left-0 z-10 flex-col justify-center px-6 md:pt-16 md:pb-6 lg:px-8 lg:pt-16 lg:pb-6 xl:px-10 overflow-hidden"
          style={{
            width: '55%',
            clipPath: 'polygon(0% 0%, 100% 0%, 90.91% 100%, 0% 100%)',
            background: 'linear-gradient(135deg, #fdfbf7 0%, #ffffff 40%, #faf7f2 70%, #fdfbf7 100%)',
          }}
        >
          {/* ── Warm glow bleeding from the diagonal edge ── */}
          <div
            aria-hidden="true"
            className="absolute inset-y-0 -right-10 w-[35%] pointer-events-none"
            style={{
              background: 'linear-gradient(to left, rgba(251,191,36,0.08) 0%, rgba(249,115,22,0.04) 30%, transparent 100%)',
            }}
          />

          {/* ── Faint dot grid — scholarly paper feel ── */}
          <div
            aria-hidden="true"
            className="absolute inset-0 pointer-events-none"
            style={{
              backgroundImage: 'radial-gradient(circle, rgba(160,140,110,0.08) 1px, transparent 1px)',
              backgroundSize: '40px 40px',
              maskImage: 'radial-gradient(ellipse 80% 70% at 30% 50%, black 20%, transparent 70%)',
              WebkitMaskImage: 'radial-gradient(ellipse 80% 70% at 30% 50%, black 20%, transparent 70%)',
            }}
          />

          <div className="max-w-2xl mx-auto w-full">
            {logo && (
              <motion.header variants={itemVariants}>
                <div className="flex flex-col items-start">
                  <img
                    src={logo.url}
                    alt={logo.alt}
                    className="h-48 lg:h-56 xl:h-64 2xl:h-72 max-h-[30vh]"
                  />
                </div>
              </motion.header>
            )}
            <motion.main variants={containerVariants}>
              <motion.h1 className="text-2xl font-bold leading-tight text-academic-text md:text-3xl lg:text-4xl xl:text-5xl" variants={itemVariants}>
                {title}
              </motion.h1>
              {slogan && (
                <motion.p className="text-base md:text-lg lg:text-xl text-academic-muted leading-snug mt-1" variants={itemVariants}>
                  {slogan}
                </motion.p>
              )}
              <motion.p className="mt-2 mb-2 lg:mb-4 text-sm text-academic-muted leading-snug md:text-base" variants={itemVariants}>
                {subtitle}
              </motion.p>
              {ctaArea ? (
                <motion.div variants={itemVariants} className="flex flex-col gap-2.5">
                  {ctaArea}
                </motion.div>
              ) : (
                <motion.a
                  href={callToAction.href}
                  className="inline-flex items-center gap-2 text-sm md:text-base font-bold tracking-widest text-primary-600 transition-colors hover:text-primary-700 uppercase"
                  variants={itemVariants}
                >
                  {callToAction.text}
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14"></path>
                    <path d="m12 5 7 7-7 7"></path>
                  </svg>
                </motion.a>
              )}
            </motion.main>
            <motion.footer className="mt-2 lg:mt-4 pt-2 lg:pt-3 border-t border-academic-muted/20" variants={itemVariants}>
              <div className="flex flex-wrap gap-x-3 lg:gap-x-4 gap-y-0.5 text-[10px] sm:text-xs text-academic-muted">
                {contactInfo.map((info, index) => (
                  <div key={index} className="flex items-center">
                    <InfoIcon type={info.type} />
                    {info.href ? (
                      <a href={info.href} target="_blank" rel="noopener noreferrer" className="hover:text-primary-600 transition-colors">
                        {info.label}
                      </a>
                    ) : (
                      <span>{info.label}</span>
                    )}
                  </div>
                ))}
              </div>
            </motion.footer>
          </div>
        </div>

      </motion.section>
    );
  }
);

HeroSection.displayName = "HeroSection";

export { HeroSection };
