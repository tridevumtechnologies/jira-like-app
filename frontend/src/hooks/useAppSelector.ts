import { useSelector, type TypedUseSelectorHook } from 'react-redux'
import type { RootState } from '@/store'

/** Typed version of useSelector — use everywhere instead of plain useSelector. */
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector
