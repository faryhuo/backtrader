/**
 * Unit tests for paramUtils utility functions
 */
import { describe, it, expect } from 'vitest'
import { coerceParamValue } from '../paramUtils'

describe('paramUtils', () => {
    describe('coerceParamValue', () => {
        describe('integer type', () => {
            it('should parse integer string correctly', () => {
                expect(coerceParamValue('int', '42')).toBe(42)
                expect(coerceParamValue('int', '0')).toBe(0)
                expect(coerceParamValue('int', '-10')).toBe(-10)
            })

            it('should handle already numeric values', () => {
                expect(coerceParamValue('int', 42)).toBe(42)
            })

            it('should truncate float strings to integer', () => {
                expect(coerceParamValue('int', '3.14159')).toBe(3)
                expect(coerceParamValue('int', '9.99')).toBe(9)
            })

            it('should return 0 for invalid values', () => {
                expect(coerceParamValue('int', '')).toBe(0)
                expect(coerceParamValue('int', 'abc')).toBe(0)
                expect(coerceParamValue('int', null)).toBe(0)
                expect(coerceParamValue('int', undefined)).toBe(0)
            })
        })

        describe('float type', () => {
            it('should parse float string correctly', () => {
                expect(coerceParamValue('float', '3.14')).toBeCloseTo(3.14)
                expect(coerceParamValue('float', '0.001')).toBeCloseTo(0.001)
                expect(coerceParamValue('float', '-2.5')).toBeCloseTo(-2.5)
            })

            it('should handle integer strings', () => {
                expect(coerceParamValue('float', '42')).toBe(42)
            })

            it('should handle already numeric values', () => {
                expect(coerceParamValue('float', 3.14)).toBeCloseTo(3.14)
            })

            it('should return 0 for invalid values', () => {
                expect(coerceParamValue('float', '')).toBe(0)
                expect(coerceParamValue('float', 'abc')).toBe(0)
                expect(coerceParamValue('float', null)).toBe(0)
                expect(coerceParamValue('float', undefined)).toBe(0)
            })
        })

        describe('other types', () => {
            it('should return value as-is for string type', () => {
                expect(coerceParamValue('string', 'hello')).toBe('hello')
                expect(coerceParamValue('string', '123')).toBe('123')
            })

            it('should return value as-is for boolean type', () => {
                expect(coerceParamValue('boolean', true)).toBe(true)
                expect(coerceParamValue('boolean', false)).toBe(false)
            })

            it('should return value as-is for unknown types', () => {
                expect(coerceParamValue('custom', 'value')).toBe('value')
                expect(coerceParamValue(null, 'value')).toBe('value')
                expect(coerceParamValue(undefined, 'value')).toBe('value')
            })

            it('should preserve objects and arrays', () => {
                const obj = { a: 1 }
                const arr = [1, 2, 3]
                expect(coerceParamValue('object', obj)).toBe(obj)
                expect(coerceParamValue('array', arr)).toBe(arr)
            })
        })
    })
})
