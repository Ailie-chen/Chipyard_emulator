// See LICENSE for license details.
package nvidia.blocks.dla

import chisel3._
import freechips.rocketchip.config.Field
import freechips.rocketchip.subsystem.BaseSubsystem
import freechips.rocketchip.diplomacy.{LazyModule,BufferParams}
import freechips.rocketchip.tilelink.{TLBuffer, TLIdentityNode}

case object NVDLAKey extends Field[Option[NVDLAParams]](None)
case object NVDLAFrontBusExtraBuffers extends Field[Int](0)

trait CanHavePeripheryNVDLA { this: BaseSubsystem =>
  p(NVDLAKey).map { params =>
    val nvdla = LazyModule(new NVDLA(params))

    fbus.fromMaster(name = Some("nvdla_dbb"), buffer = BufferParams.default) {
      TLBuffer.chainNode(p(NVDLAFrontBusExtraBuffers))
    } := nvdla.dbb_tl_node

    pbus.toFixedWidthSingleBeatSlave(4, Some("nvdla_cfg")) { nvdla.cfg_tl_node }

    ibus.fromSync := nvdla.int_node
  }
}
