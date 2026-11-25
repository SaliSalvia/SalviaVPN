//go:build !windows && !linux

package main

import "errors"

// run runs a command; the TUN service is written for Windows and Linux.
func run(string, []string) int {
	return fail(errors.New("the TUN mode is not available on this system"))
}
