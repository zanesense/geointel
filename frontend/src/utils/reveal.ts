import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

type RevealOptions = {
  from?: gsap.TweenVars;
  to?: gsap.TweenVars;
  stagger?: number;
  trigger?: string | Element;
};

const defaults = {
  from: { opacity: 0, y: 30 },
  to: { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' },
};

export function useReveal<T extends HTMLElement>(opts: RevealOptions = {}) {
  const ref = useRef<T>(null!);
  const { from, to, stagger, trigger } = opts;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) return;

    const ctx = gsap.context(() => {
      const targets = stagger ? el.children : el;
      gsap.set(targets, { ...defaults.from, ...from });
      gsap.to(targets, {
        ...defaults.to,
        ...to,
        stagger,
        scrollTrigger: {
          trigger: trigger ? (typeof trigger === 'string' ? document.querySelector(trigger) : trigger) : el,
          start: 'top 90%',
          toggleActions: 'play none none reverse',
        },
      });
    }, el);

    return () => ctx.revert();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return ref;
}
