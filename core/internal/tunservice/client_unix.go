//go:build linux

package tunservice

import (
	"os"
	"strconv"
	"time"

	"github.com/salvia-vpn/salvia-vpn-client/core/internal/tunapi"
)

// InstallForUser installs the service for the user running this process
// (as root through sudo, for the user who ran sudo), asking for the
// administrator's permission.
func InstallForUser() error {
	uid := strconv.Itoa(os.Getuid())
	if os.Geteuid() == 0 {
		if sudo := os.Getenv("SUDO_UID"); sudo != "" && uid == "0" {
			uid = sudo
		}
		return Install(uid)
	}
	return runElevated("install-as-admin", "-user", uid)
}

// UninstallForUser removes the service: through its socket while it runs,
// with no prompt; else as the administrator.
func UninstallForUser() error {
	if installed, err := tunapi.Installed(); err == nil && !installed {
		return nil
	}
	if err := askService(tunapi.Message{Type: tunapi.TypeUninstall}, tunapi.TypeUninstalling); err == nil {
		return waitRemoved(30 * time.Second)
	}
	if os.Geteuid() == 0 {
		return Uninstall()
	}
	return runElevated("uninstall-as-admin")
}

// reportFile makes the file an elevated copy writes why it failed to, and
// returns a function that removes it.
func reportFile() (string, func(), error) {
	f, err := os.CreateTemp("", "salvia-vpn-tun-*.txt")
	if err != nil {
		return "", nil, err
	}
	f.Close()
	return f.Name(), func() { os.Remove(f.Name()) }, nil
}
