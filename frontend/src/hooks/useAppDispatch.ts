import { useDispatch } from 'react-redux'
import type { AppDispatch } from '@/store'

/** Typed version of useDispatch — use everywhere instead of plain useDispatch. */
export const useAppDispatch = () => useDispatch<AppDispatch>()
